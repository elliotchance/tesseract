-- This file contains Lua code that is to be included in all compilations.

local function no_such_operator(left, operator, right)
    error(string.format('No such operator %s %s %s.', type(left), operator,
        type(right)))
end

local function no_such_mono_operator(operator, right)
    error(string.format('No such operator %s %s.', operator, type(right)))
end

local function no_such_function(name, arg)
    error(string.format('No such function %s(%s).', name, type(arg)))
end

local function no_such_type(type)
    error(string.format("No such type '%s'.", type))
end

local function zrangeall(key)
    local bulk = redis.call('ZRANGE', key, '0', '-1', 'WITHSCORES')
	local result = {}
	local nextkey
	for i, v in ipairs(bulk) do
		if i % 2 == 1 then
			nextkey = v
		else
			result[nextkey] = v
		end
	end
	return result
end

-- nil values in Lua that are inside of a table will not exist as elements. For
-- example if we had { row["foo"] } and the "foo" key did not exist the table
-- would consist of zero elements which causes all sorts of logic to go wrong.
-- All row accesses are run through this method so we can force a SQL NULL to
-- come out for missing values.
local function f(row, path)
    if row[path] == nil then
        return cjson.null
    end

    return row[path]
end
