local function operator_like(value, regex)
    regex = '^' .. regex:gsub('%%', '.+') .. '$'
    return value:find(regex) ~= nil
end
