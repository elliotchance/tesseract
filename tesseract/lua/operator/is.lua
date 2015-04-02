local function operator_is(left, right)
    if right == 'number' then
        return type(left) == 'number';
    end
    return left == cjson.null or left == nil
end
