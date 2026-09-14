package management

import (
	"net/http"
	"runtime"
	"sync/atomic"
	"time"

	"github.com/gin-gonic/gin"
)

// Independent lock models for dashboard display
var independentLockModels = []string{
	"claude-opus-4-6",
	"claude-opus-4-6-thinking",
	"gemini-3.1-flash-lite",
	"gemini-3.5-flash-lite",
	"gemini-3.6-flash-high",
	"gemini-3.7-flash-high",
	"gemini-3.8-flash-high",
	"gemini-3-flash",
	"gemini-3.1-flash-image",
	"gemini-3.1-pro-low",
}

// Rate limiter state
var (
	requestSuccessCount  atomic.Int64
	requestWindowStart   atomic.Int64
	requestPerMinuteLimit atomic.Int64
)

func init() {
	requestPerMinuteLimit.Store(1000) // default 1000 per minute
	requestWindowStart.Store(time.Now().UnixMilli())
}

// CheckRequestRateLimit checks if the per-minute success limit is exceeded.
// Returns true if the request should be rejected.
func CheckRequestRateLimit() bool {
	limit := requestPerMinuteLimit.Load()
	if limit <= 0 {
		return false
	}
	now := time.Now().UnixMilli()
	windowStart := requestWindowStart.Load()
	if now-windowStart > 60000 {
		// Reset window
		requestSuccessCount.Store(0)
		requestWindowStart.Store(now)
		return false
	}
	return requestSuccessCount.Load() >= limit
}

// RecordSuccessRequest increments the success counter.
func RecordSuccessRequest() {
	requestSuccessCount.Add(1)
}

// GetDashboardStats returns 403 counts, independent lock model availability, and memory usage.
func (h *Handler) GetDashboardStats(c *gin.Context) {
	if h == nil || h.authManager == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "auth manager unavailable"})
		return
	}

	now := time.Now()
	auths := h.authManager.List()

	totalAccounts := len(auths)
	availableAccounts := 0
	disabledAccounts := 0
	forbiddenAccounts := 0
	var forbiddenList []gin.H

	// Per independent-lock-model availability
	modelAvailable := make(map[string]int)
	modelTotal := make(map[string]int)
	modelLocked := make(map[string]int)
	for _, m := range independentLockModels {
		modelAvailable[m] = 0
		modelTotal[m] = 0
		modelLocked[m] = 0
	}

	var lockedAccountsList []gin.H
	for _, auth := range auths {
		if auth == nil {
			continue
		}
		if auth.Disabled {
			disabledAccounts++
			continue
		}

		// Check if account has 403 error
		is403 := false
		if auth.LastError != nil {
			code := auth.LastError.HTTPStatus
			if code == 403 {
				is403 = true
				forbiddenAccounts++
				email := ""
				rt := ""
				if auth.Metadata != nil {
					if e, ok := auth.Metadata["email"].(string); ok {
						email = e
					}
					if r, ok := auth.Metadata["refresh_token"].(string); ok {
						rt = r
					}
				}
				forbiddenList = append(forbiddenList, gin.H{
					"name":  auth.FileName,
					"email": email,
					"rt":    rt,
				})
			}
		}

		if !is403 {
			availableAccounts++
		}

		// Check each independent lock model
		for _, modelName := range independentLockModels {
			modelTotal[modelName]++
			if auth.ModelStates != nil {
				if state, ok := auth.ModelStates[modelName]; ok && state != nil {
					if state.Unavailable && !state.NextRetryAfter.IsZero() && state.NextRetryAfter.After(now) {
						modelLocked[modelName]++
						continue
					}
				}
			}
			if !is403 {
				modelAvailable[modelName]++
			}
		}
		// Track locked accounts
		if auth.ModelStates != nil {
			hasLock := false
			mlocks := make([]gin.H, 0)
			for _, mn := range independentLockModels {
				st, ok := auth.ModelStates[mn]
				if ok && st != nil && !st.NextRetryAfter.IsZero() && st.NextRetryAfter.After(now) {
					hasLock = true
					mlocks = append(mlocks, gin.H{"model": mn, "locked": true, "expires": st.NextRetryAfter, "remaining_seconds": int(st.NextRetryAfter.Sub(now).Seconds())})
				} else {
					mlocks = append(mlocks, gin.H{"model": mn, "locked": false})
				}
			}
			if hasLock {
				lockedAccountsList = append(lockedAccountsList, gin.H{"name": auth.FileName, "models": mlocks})
			}
		}

	}
	// Model stats
	modelStats := make([]gin.H, 0, len(independentLockModels))
	for _, modelName := range independentLockModels {
		modelStats = append(modelStats, gin.H{
			"model":     modelName,
			"total":     modelTotal[modelName],
			"available": modelAvailable[modelName],
			"locked":    modelLocked[modelName],
		})
	}

	// Memory stats
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	c.JSON(http.StatusOK, gin.H{
		"observed_at":        now,
		"total_accounts":    totalAccounts,
		"available_accounts": availableAccounts,
		"disabled_accounts": disabledAccounts,
		"forbidden_accounts": forbiddenAccounts,
		"forbidden_list":    forbiddenList,
		"model_stats":       modelStats,
		"memory": gin.H{
			"alloc_mb":       memStats.Alloc / 1024 / 1024,
			"sys_mb":         memStats.Sys / 1024 / 1024,
			"heap_inuse_mb":  memStats.HeapInuse / 1024 / 1024,
			"heap_objects":   memStats.HeapObjects,
			"goroutines":    runtime.NumGoroutine(),
		},
		"locked_accounts": lockedAccountsList,
		"rate_limit": gin.H{
			"success_count":    requestSuccessCount.Load(),
			"limit_per_minute": requestPerMinuteLimit.Load(),
		},
	})
}

// GetRequestRateLimit returns current rate limit settings.
func (h *Handler) GetRequestRateLimit(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"limit_per_minute": requestPerMinuteLimit.Load(),
		"success_count":    requestSuccessCount.Load(),
		"window_start":     requestWindowStart.Load(),
	})
}

// SetRequestRateLimit updates the per-minute success limit.
func (h *Handler) SetRequestRateLimit(c *gin.Context) {
	var req struct {
		Limit int64 `json:"limit"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}
	if req.Limit < 0 {
		req.Limit = 0
	}
	requestPerMinuteLimit.Store(req.Limit)
	requestSuccessCount.Store(0)
	requestWindowStart.Store(time.Now().UnixMilli())
	c.JSON(http.StatusOK, gin.H{"status": "ok", "limit_per_minute": req.Limit})
}

// GetMemoryStats returns current memory usage.
func (h *Handler) GetMemoryStats(c *gin.Context) {
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	c.JSON(http.StatusOK, gin.H{
		"alloc_mb":       memStats.Alloc / 1024 / 1024,
		"total_alloc_mb": memStats.TotalAlloc / 1024 / 1024,
		"sys_mb":         memStats.Sys / 1024 / 1024,
		"heap_alloc_mb":  memStats.HeapAlloc / 1024 / 1024,
		"heap_inuse_mb":  memStats.HeapInuse / 1024 / 1024,
		"heap_objects":   memStats.HeapObjects,
		"goroutines":    runtime.NumGoroutine(),
		"gc_cycles":     memStats.NumGC,
	})
}

// Memory limit in bytes (0 = no limit)
var memoryLimitBytes atomic.Int64

// DeleteForbiddenAccounts removes all accounts with 403 status and returns the list.
func (h *Handler) DeleteForbiddenAccounts(c *gin.Context) {
	if h == nil || h.authManager == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "auth manager unavailable"})
		return
	}

	auths := h.authManager.List()
	var removed []gin.H
	for _, auth := range auths {
		if auth == nil || auth.Disabled {
			continue
		}
		if auth.LastError != nil && auth.LastError.HTTPStatus == 403 {
			email := ""
			rt := ""
			if auth.Metadata != nil {
				if e, ok := auth.Metadata["email"].(string); ok {
					email = e
				}
				if r, ok := auth.Metadata["refresh_token"].(string); ok {
					rt = r
				}
			}
			removed = append(removed, gin.H{
				"name":  auth.FileName,
				"email": email,
				"rt":    rt,
			})
			h.authManager.Remove(c.Request.Context(), auth.ID)
		}
	}
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"removed": len(removed),
		"list":    removed,
	})
}

// GetMemoryLimit returns current memory limit.
func (h *Handler) GetMemoryLimit(c *gin.Context) {
	limitMB := memoryLimitBytes.Load() / 1024 / 1024
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	c.JSON(http.StatusOK, gin.H{
		"limit_mb":   limitMB,
		"current_mb": memStats.Alloc / 1024 / 1024,
		"sys_mb":     memStats.Sys / 1024 / 1024,
	})
}

// SetMemoryLimit sets memory limit in GB.
func (h *Handler) SetMemoryLimit(c *gin.Context) {
	var req struct {
		LimitGB float64 `json:"limit_gb"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}
	if req.LimitGB < 0 {
		req.LimitGB = 0
	}
	bytes := int64(req.LimitGB * 1024 * 1024 * 1024)
	memoryLimitBytes.Store(bytes)
	c.JSON(http.StatusOK, gin.H{"status": "ok", "limit_gb": req.LimitGB})
}

// CheckMemoryLimit checks if memory usage exceeds the configured limit.
// Returns true if limit exceeded.
func CheckMemoryLimit() bool {
	limit := memoryLimitBytes.Load()
	if limit <= 0 {
		return false
	}
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	return int64(memStats.Alloc) > limit
}
