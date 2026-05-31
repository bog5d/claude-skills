# Cache Health Monitoring Integration

## Cron Job

```
Name:   cache-health-report
ID:     16a9c651c8c7
Schedule: every 6h
Script: /Users/mac/.hermes/profiles/her-m2/bin/cache_monitor.py her-m2
Skills: deepseek-cache-optimization
Deliver: local
```

Reports:
- Total API calls (24h)
- Estimated cache hits / misses
- Cache hit rate %
- Model in use
- Skills change frequency warning (if >5 changes in 24h)

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Cache hit rate | <60% | <30% |
| Skill changes/24h | >5 | >15 |
| Agent.log size | >10MB | >50MB |

## Integration with system-watchdog

The system-watchdog already checks log sizes (>50MB auto-truncate).
Cache monitoring is separate (6h cron) to avoid token waste on frequent checks.
