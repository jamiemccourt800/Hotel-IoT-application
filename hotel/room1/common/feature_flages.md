# Feature Flags Implementation

**GitLab Feature Flags for Hotel IoT Simulator**  
**Task**: DGP-139 | **Updated**: Dec 5, 2025

---

## 🚀 Quick Start

**1. Create `.env` in `hotel/`:**
```bash
UNLEASH_URL=<your-gitlab-unleash-api-url>
UNLEASH_INSTANCE_ID=<your-instance-id>
UNLEASH_APP_NAME=actuator
```
> Get URL and Instance ID from GitLab: Deploy → Feature Flags → Configure

**2. Start services:**
```bash
docker compose -f docker-compose.hotel1.yml up
```

**3. Toggle flags:** GitLab → Deploy → Feature Flags (changes apply in ~30s)

---

## 📖 Overview

**What**: Runtime control of actuator behavior via GitLab UI  
**Why**: Zero-downtime feature toggles, gradual rollouts, emergency kill switches  
**How**: GitLab Unleash API → FeatureFlags wrapper → Actuators poll every 15s

---

## 🎛️ Available Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `external_control` | Process MQTT commands | `True` |
| `local_control` | Run autonomous control loop | `True` |
| `ack_publishing` | Publish acknowledgment messages | `True` |
| `adaptive_control` | Adaptive PID tuning (future) | `True` |

---

## 🔧 GitLab Setup

1. Go to GitLab project → **Deploy** → **Feature Flags**
2. Click **Configure** to get API URL and Instance ID
3. Create flags: `external_control`, `local_control`, `ack_publishing`
4. Copy credentials to `.env` file (see Quick Start)

⚠️ **Never commit Instance ID to git** - use `.env` (local) or Secrets (K8s)

---

## 💻 Code Usage

**Import and initialize:**
```python
from common import FeatureFlags

self.feature_flags = FeatureFlags(device_config)
```

**Check flags:**
```python
# External control
if self.feature_flags.is_enabled('external_control'):
    self.process_command(command)

# Local control
if self.feature_flags.is_enabled('local_control'):
    self.run_control_loop()

# Acknowledgments
if self.feature_flags.is_enabled('ack_publishing'):
    self.send_ack(command, status)
```

**Cleanup:**
```python
finally:
    self.feature_flags.shutdown()
```

---

## ☸️ Kubernetes Deployment

**ConfigMap** (`unleash-cm.yaml`):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: unleash-config
data:
  unleash-url: "<your-gitlab-unleash-api-url>"
  unleash-app-name: "actuator"
```

**Secret** (`unleash-secret.yaml`):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: unleash-secret
type: Opaque
stringData:
  instance-id: "<your-instance-id>"
```

**Deployment** (inject env vars):
```yaml
env:
  - name: UNLEASH_URL
    valueFrom:
      configMapKeyRef:
        name: unleash-config
        key: unleash-url
  - name: UNLEASH_INSTANCE_ID
    valueFrom:
      secretKeyRef:
        name: unleash-secret
        key: instance-id
  - name: UNLEASH_APP_NAME
    valueFrom:
      configMapKeyRef:
        name: unleash-config
        key: unleash-app-name
```

**Apply:**
```bash
kubectl apply -f unleash-cm.yaml
kubectl apply -f unleash-secret.yaml
kubectl apply -f <actuator>-depl.yaml
```

---

## 🧪 Testing

**Automated (30 tests):**
```bash
# All tests
python run_feature_flag_tests.py --coverage

# Unit tests only (17 tests)
python -m pytest tests/unit/hotel/common/test_feature_flags.py -v

# Integration tests (13 tests)
python -m pytest tests/integration/test_feature_flags_integration.py -v
```

**Manual testing:**
```bash
# 1. Start services
docker compose -f docker-compose.hotel1.yml up -d

# 2. Send command
mosquitto_pub -t "hotel/hotel_01/101/temperature/control" \
  -m '{"action":"set_target","value":23.5}'

# 3. Toggle flag in GitLab UI

# 4. Wait 30s and send command again

# 5. Check logs for behavior change
docker compose logs temperature-actuator | grep external-control
```

---

## ➕ Adding New Flags

1. Create flag in GitLab (Deploy → Feature Flags)
2. Add check in code: `if self.feature_flags.is_enabled('new_flag'):`
3. Write test
4. Deploy

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "unleash-disabled" in logs | Check all 3 env vars set: `UNLEASH_URL`, `UNLEASH_INSTANCE_ID`, `UNLEASH_APP_NAME` |
| Flags not updating | Wait 30s for polling interval |
| 403 Forbidden | Verify `UNLEASH_INSTANCE_ID` is correct |
| Always returns True | Check flag names are exact match (case-sensitive) |

**Debug commands:**
```bash
# Check env vars
docker exec <container> env | grep UNLEASH
kubectl exec <pod> -- env | grep UNLEASH

# Check logs
docker logs <container> | grep unleash
kubectl logs <pod> | grep unleash

# Test API
curl -H "UNLEASH-INSTANCEID: $UNLEASH_INSTANCE_ID" $UNLEASH_URL
```

---

## 📊 Summary

**Deliverables:** ✅ Complete
- FeatureFlags wrapper (`hotel/room1/common/feature_flags.py`)
- 3 actuators updated (temperature, humidity, light)
- 30 automated tests (all passing)
- K8s ConfigMap/Secret templates
- This documentation

**Status:** Production ready

---

## 📚 References

- **Code**: `hotel/room1/common/feature_flags.py`
- **Tests**: `tests/unit/hotel/common/test_feature_flags.py`
- **Manual Testing**: `tests/FEATURE_FLAG_TESTING_GUIDE.md`
- **GitLab Docs**: https://docs.gitlab.com/ee/operations/feature_flags.html
- **Unleash Client**: https://github.com/Unleash/unleash-client-python
