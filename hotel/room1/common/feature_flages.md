# Feature Flags Implementation

**GitLab Feature Flags for Hotel IoT Simulator**  

---

## Quick Start

**1. Create `.env` in `hotel/`:**
```bash
UNLEASH_URL=<gitlab-unleash-api-url>
UNLEASH_INSTANCE_ID=<instance-id>
UNLEASH_APP_NAME=actuator
```
> Get URL and Instance ID from GitLab: Deploy → Feature Flags → Configure

**2. Start services:**
```bash
docker compose -f docker-compose.hotel1.yml up
```

**3. Toggle flags:** GitLab → Deploy → Feature Flags (changes apply in ~30s)

---

## Overview

**What**: Runtime control of actuator behavior via GitLab UI  
**Why**: Zero-downtime feature toggles, gradual rollouts, emergency kill switches  
**How**: GitLab Unleash API → FeatureFlags wrapper → Actuators poll every 15s

---

## Available Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `external_control` | Process MQTT commands | `True` |
| `local_control` | Run autonomous control loop | `True` |
| `ack_publishing` | Publish acknowledgment messages | `True` |

---

## GitLab Setup

1. Go to GitLab project → **Deploy** → **Feature Flags**
2. Click **Configure** to get API URL and Instance ID
3. Create flags: `external_control`, `local_control`, `ack_publishing`
4. Copy credentials to `.env` file (see Quick Start)

**Never commit Instance ID to git** - use `.env` (local) or Secrets (K8s)

---

## Kubernetes Deployment

**Apply:**
```bash
kubectl apply -f unleash-cm.yaml
kubectl apply -f unleash-secret.yaml
kubectl apply -f <actuator>-depl.yaml
```

---

## Testing

**Automated (30 tests):**


---

## Adding New Flags

1. Create flag in GitLab (Deploy → Feature Flags)
2. Add check in code: `if self.feature_flags.is_enabled('new_flag'):`
3. Write test
4. Deploy

---

## Summary

**Deliverables:**
- FeatureFlags wrapper (`hotel/room1/common/feature_flags.py`)
- 3 actuators updated (temperature, humidity, light)
- 30 automated tests (all passing)
- K8s ConfigMap/Secret templates
- This documentation

---

## References

- **Code**: `hotel/room1/common/feature_flags.py`
- **Tests**: `tests/unit/hotel/common/test_feature_flags.py`
- **Manual Testing**: `tests/FEATURE_FLAG_TESTING_GUIDE.md`
- **GitLab Docs**: https://docs.gitlab.com/ee/operations/feature_flags.html
- **Unleash Client**: https://github.com/Unleash/unleash-client-python