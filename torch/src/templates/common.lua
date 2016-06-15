local t = require "torch"
local util = require "dddt.util"
local common = {}
-- Param
local function parsename(x)
  -- Expects parameter name in form name_1,2,3,
  local splitted = util.split(x,"_")
  assert(#splitted == 2)
  local id = splitted[1]
  local shape_str = util.split(splitted[2], ",")
  local shape = util.map(tonumber, shape_str)
  return id, shape
end

local function default_index(tbl, k)
  print("generating paramter values")
  local id, shape = parsename(k)
  local new_val = t.rand(t.LongStorage(shape)) * 0.1
  tbl[k] = new_val
  return new_val
end

function common.gen_param()
  local param = {}
  setmetatable(param,{
    __index = function(param,k) return default_index(param, k) end
  })
  return param
end

function common.param_str(id, shape)
  return "%s_%s" % {id, util.tostring(shape)}
end

return common