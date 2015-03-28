local function operator_like(value, regex)
    regex = '^' .. regex .. '$'
    return value:find(regex) ~= nil
end
