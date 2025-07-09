# TauseStack Framework - TODOs Granulares

## 🎯 **CURRENT SPRINT: MCP Server Implementation**

### **P0 - Critical (This Week)**

#### **MCP Server Foundation**
- [ ] **MCP-001**: Create `/tausestack/mcp/server/` directory structure
  - **Acceptance**: Directory exists with `__init__.py`, `core.py`, `tools.py`
  - **Dependencies**: None
  - **Estimate**: 30 min
  - **Tests**: Directory structure test

- [ ] **MCP-002**: Implement basic MCP server protocol
  - **File**: `/tausestack/mcp/server/core.py`
  - **Function**: `class MCPServer` with `start()`, `stop()`, `register_tool()`
  - **Dependencies**: MCP-001
  - **Estimate**: 2 hours
  - **Tests**: MCP server can start/stop

- [ ] **MCP-003**: Expose storage service as MCP tool
  - **File**: `/tausestack/mcp/server/tools.py`
  - **Function**: `@mcp_tool("storage/json/get")` and `@mcp_tool("storage/json/put")`
  - **Dependencies**: MCP-002
  - **Estimate**: 1 hour
  - **Tests**: Can get/put via MCP protocol

#### **Existing Service Integration (DO NOT MODIFY SERVICES)**
- [ ] **MCP-004**: Add MCP wrapper to analytics service
  - **File**: `/tausestack/mcp/server/analytics_tools.py`
  - **Function**: Wrap existing `analytics.track_event()` as MCP tool
  - **Dependencies**: MCP-003
  - **Constraint**: ⚠️ DO NOT modify `/tausestack/services/analytics/`
  - **Estimate**: 45 min
  - **Tests**: MCP analytics tool works, existing analytics unchanged

- [ ] **MCP-005**: Add MCP wrapper to AI services
  - **File**: `/tausestack/mcp/server/ai_tools.py` 
  - **Function**: Wrap existing AI generation capabilities
  - **Dependencies**: MCP-004
  - **Constraint**: ⚠️ DO NOT modify `/tausestack/services/ai_services/`
  - **Estimate**: 1 hour
  - **Tests**: MCP AI tools work, existing AI services unchanged

### **P1 - High (Next Week)**

#### **MCP Client Implementation**
- [ ] **MCP-006**: Create MCP client to consume external servers
  - **File**: `/tausestack/mcp/client/core.py`
  - **Function**: `class MCPClient` with `connect()`, `call_tool()`
  - **Dependencies**: MCP-005
  - **Estimate**: 3 hours
  - **Tests**: Can connect to external MCP server

#### **Agent Framework Foundation**
- [ ] **MCP-007**: Create basic agent with MCP tools
  - **File**: `/tausestack/agents/core.py`
  - **Function**: `class Agent` that uses MCP tools
  - **Dependencies**: MCP-006
  - **Estimate**: 2 hours
  - **Tests**: Agent can use MCP tools

### **P2 - Medium (Later)**

#### **Admin MCP Dashboard**
- [ ] **MCP-008**: Add MCP status to existing admin
  - **File**: Extend existing admin dashboard
  - **Function**: Show MCP server status, tool usage
  - **Dependencies**: MCP-007
  - **Constraint**: ⚠️ EXTEND existing admin, don't rewrite
  - **Estimate**: 1.5 hours

## 🛡️ **CONSTRAINTS FOR EACH TASK**

### **Global Constraints (Apply to ALL tasks)**
- ✅ **Multi-tenant**: Every new function must accept `tenant_id`
- ✅ **Testing**: Must pass existing tests after changes
- ✅ **Examples**: All examples in `/examples/` must continue working
- ✅ **Backwards Compatibility**: Existing APIs must not break
- ❌ **No Rewrites**: Never rewrite existing working code

### **Specific Constraints**

#### **For MCP-001 to MCP-003 (Foundation)**
- ✅ **Start Small**: Basic implementation first, optimization later
- ✅ **Follow Patterns**: Use existing TauseStack patterns
- ❌ **No External Dependencies**: Use only existing dependencies

#### **For MCP-004 to MCP-005 (Service Integration)**
- ⚠️ **CRITICAL**: DO NOT modify existing services
- ✅ **Wrapper Only**: Create wrapper functions that call existing services
- ✅ **Test Both**: Test MCP tools AND ensure existing services still work

#### **For MCP-006 to MCP-007 (Client & Agents)**
- ✅ **Extensible**: Design for multiple external MCP servers
- ✅ **Error Handling**: Robust error handling for external connections
- ✅ **Per-Tenant**: Each tenant can have different MCP configurations

## 🧪 **TESTING CHECKLIST (Run After Each Task)**

### **Automated Tests**
```bash
# Must pass after EVERY task
pytest tests/                                    # Unit tests
python examples/ai_integration_demo.py          # AI integration working
python examples/multitenant_services_demo.py    # Services working
python examples/tausepro_integration_demo.py    # External integration working
```

### **Manual Verification**
- [ ] Admin dashboard loads without errors
- [ ] Existing API endpoints return expected responses
- [ ] Multi-tenant isolation still works
- [ ] New MCP functionality works as specified

## 📝 **TASK COMPLETION CRITERIA**

### **Definition of Done**
For a task to be considered complete:
1. ✅ **Code**: Implementation matches specification
2. ✅ **Tests**: All existing tests pass + new tests for new functionality
3. ✅ **Examples**: All examples still work
4. ✅ **Documentation**: Update relevant docs
5. ✅ **Integration**: Works with existing TauseStack ecosystem

### **Task Status Tracking**
- 🔴 **Not Started**: Task not begun
- 🟡 **In Progress**: Development underway
- 🟢 **Code Complete**: Implementation done, testing in progress
- ✅ **Done**: All criteria met, tested, documented

## 🚨 **ROLLBACK PLAN**

### **If Something Breaks**
1. **Immediate**: Revert last changes
2. **Verify**: Run full test suite
3. **Diagnose**: Understand what broke
4. **Fix**: Make minimal fix
5. **Test**: Verify fix doesn't break anything else

### **Rollback Commands**
```bash
# Revert last commit
git revert HEAD

# Run verification
python examples/ai_integration_demo.py
python examples/multitenant_services_demo.py

# Check admin still works
curl http://localhost:9001/dashboard/
```

## 🎯 **ACCEPTANCE CRITERIA EXAMPLES**

### **Good Acceptance Criteria** ✅
```
MCP-003: Expose storage service as MCP tool
GIVEN: TauseStack storage service is running
WHEN: I call MCP tool "storage/json/put" with tenant_id and data
THEN: Data is stored for that tenant
AND: I can retrieve it with "storage/json/get"
AND: Other tenants cannot access this data
AND: Existing storage.json.put() still works unchanged
```

### **Bad Acceptance Criteria** ❌
```
MCP-003: Make storage work with MCP
- Add MCP support
- Test it works
```

## 🔄 **CONTINUOUS VERIFICATION**

### **After Each Task**
1. **Regression**: Verify nothing broke
2. **Integration**: Verify new feature integrates properly
3. **Performance**: Verify no significant performance regression
4. **Documentation**: Update architecture docs if needed

### **Weekly Health Check**
```bash
# Run comprehensive verification
./scripts/health_check.sh

# Verify all services are healthy
curl http://localhost:9001/health

# Check examples work end-to-end
./scripts/run_all_examples.sh
```

---

## 🎯 **REMEMBER: INCREMENTAL & SAFE**

- ✅ **Small Steps**: Each task should be completable in < 3 hours
- ✅ **Testable**: Each task should be independently testable
- ✅ **Reversible**: Each task should be easily revertible
- ✅ **Additive**: Prefer adding new code over modifying existing code