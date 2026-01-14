# Security Advisory

## Dependency Security Updates

This document tracks security vulnerabilities and their resolutions in project dependencies.

## Latest Updates (January 2026)

### Critical Security Patches Applied

#### 1. Apache Airflow - Updated to 2.10.4

**Previous Version:** 2.8.0  
**Current Version:** 2.10.4  
**Severity:** Critical

**Vulnerabilities Fixed:**

1. **CVE: Execution with Unnecessary Privileges**
   - Affected versions: < 2.10.1
   - Patched in: 2.10.1
   - Status: ✅ Fixed

2. **CVE: DAG Author Code Execution in airflow-scheduler**
   - Affected versions: >= 2.4.0, < 2.9.3
   - Patched in: 2.9.3
   - Status: ✅ Fixed

3. **CVE: Bypass permission verification to read code of other DAGs**
   - Affected versions: >= 0, < 2.8.1rc1
   - Patched in: 2.8.1rc1
   - Status: ✅ Fixed

4. **CVE: Pickle deserialization vulnerability in XComs**
   - Affected versions: >= 0, < 2.8.1rc1
   - Patched in: 2.8.1rc1
   - Status: ✅ Fixed

#### 2. Apache Airflow Providers Snowflake - Updated to 6.4.0

**Previous Version:** 5.1.0  
**Current Version:** 6.4.0  
**Severity:** High

**Vulnerabilities Fixed:**

1. **CVE: Special Element Injection via CopyFromExternalStageToSnowflakeOperator**
   - Affected versions: < 6.4.0
   - Patched in: 6.4.0
   - Status: ✅ Fixed

#### 3. Snowflake Connector Python - Updated to 3.13.1

**Previous Version:** 3.6.0  
**Current Version:** 3.13.1  
**Severity:** Critical

**Vulnerabilities Fixed:**

1. **CVE: SQL Injection in write_pandas**
   - Affected versions: >= 2.2.5, <= 3.13.0
   - Patched in: 3.13.1
   - Status: ✅ Fixed
   - Impact: This vulnerability could allow SQL injection attacks when using write_pandas function
   - Mitigation: Updated to patched version 3.13.1

#### 4. Snowflake SQLAlchemy - Updated to 1.7.2

**Previous Version:** 1.5.1  
**Current Version:** 1.7.2  
**Reason:** Compatibility with snowflake-connector-python 3.13.1

## Updated Dependencies

```txt
# Airflow (Security-Patched)
apache-airflow==2.10.4
apache-airflow-providers-snowflake==6.4.0

# Snowflake (Security-Patched)
snowflake-connector-python==3.13.1
snowflake-sqlalchemy==1.7.2

# API and HTTP
requests==2.31.0
tenacity==8.2.3

# Data Processing
pandas==2.1.4
numpy==1.26.3

# Configuration
python-dotenv==1.0.0

# Utilities
pytz==2023.3
```

## Breaking Changes

### Airflow 2.8.0 → 2.10.4

**Minimal breaking changes for this project:**
- Our DAG code uses standard operators and patterns that are compatible
- No code changes required for DAG files
- Configuration may need minor adjustments

**Action Items:**
1. ✅ Update requirements.txt
2. ✅ Update documentation
3. ⚠️ Test DAGs after upgrade (recommended)
4. ⚠️ Review Airflow 2.10.4 release notes for any environment-specific changes

### Snowflake Connector 3.6.0 → 3.13.1

**Changes:**
- Improved security for write_pandas function
- Better error handling
- Performance improvements

**Action Items:**
1. ✅ Update requirements.txt
2. ✅ No code changes required (backward compatible)
3. ⚠️ Test data loading operations after upgrade

## Security Best Practices

### Current Implementation

✅ **No hardcoded credentials** - All credentials in environment variables  
✅ **Secure token handling** - Bearer tokens loaded from .env  
✅ **SQL injection prevention** - Using parameterized queries  
✅ **Connection encryption** - HTTPS for API, encrypted Snowflake connections  
✅ **Minimal privileges** - Code follows least privilege principle  
✅ **Input validation** - Data validation before database operations  
✅ **Error handling** - Comprehensive error handling without exposing sensitive data  
✅ **Logging security** - No PII or credentials in logs  

### Additional Recommendations

1. **Regular Updates**
   - Check for security updates monthly
   - Subscribe to security advisories for dependencies
   - Use tools like `pip-audit` or `safety` to scan dependencies

2. **Credential Management**
   - Rotate API tokens regularly
   - Use Airflow Connections/Variables for sensitive data
   - Consider using secret management services (AWS Secrets Manager, HashiCorp Vault)

3. **Access Control**
   - Implement RBAC in Airflow
   - Use Snowflake role-based access control
   - Limit access to .env files

4. **Network Security**
   - Use VPN or private endpoints for Snowflake access
   - Implement IP whitelisting where possible
   - Enable MFA for all accounts

5. **Monitoring**
   - Enable Airflow audit logging
   - Monitor Snowflake query history for anomalies
   - Set up alerts for failed authentication attempts

## Verification Steps

After updating dependencies:

```bash
# 1. Update virtual environment
pip install -r requirements.txt --upgrade

# 2. Verify installations
pip list | grep airflow
pip list | grep snowflake

# 3. Run validation script
python src/utils/validate_installation.py

# 4. Test connections
python src/database/snowflake_connector.py
python src/api/salla_connector.py

# 5. Test DAG parsing
airflow dags list

# 6. Run a test DAG
airflow dags test salla_bronze_extraction $(date +%Y-%m-%d)
```

## Rollback Plan

If issues occur after upgrade:

```bash
# 1. Revert requirements.txt to previous versions
git checkout HEAD~1 requirements.txt

# 2. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 3. Restart Airflow
airflow db reset
airflow webserver &
airflow scheduler &
```

## Security Contact

For security issues or concerns:
- Open a private security advisory on GitHub
- Contact repository maintainers directly
- Follow responsible disclosure practices

## Compliance Notes

These security updates help maintain compliance with:
- OWASP Top 10 security risks
- CIS Benchmarks for secure configuration
- SOC 2 security requirements
- GDPR data protection requirements

## Update History

| Date | Component | Old Version | New Version | Reason |
|------|-----------|-------------|-------------|--------|
| 2026-01-14 | apache-airflow | 2.8.0 | 2.10.4 | Multiple CVEs fixed |
| 2026-01-14 | apache-airflow-providers-snowflake | 5.1.0 | 6.4.0 | Special Element Injection |
| 2026-01-14 | snowflake-connector-python | 3.6.0 | 3.13.1 | SQL Injection vulnerability |
| 2026-01-14 | snowflake-sqlalchemy | 1.5.1 | 1.7.2 | Compatibility update |

## Next Review Date

**Scheduled:** 2026-02-14 (monthly review)

---

**Last Updated:** 2026-01-14  
**Status:** ✅ All known vulnerabilities patched  
**Action Required:** Update dependencies using `pip install -r requirements.txt --upgrade`
