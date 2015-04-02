local function operator_is(left, right)
    if right == 'true' then
        return left == true;
    end
    if right == 'number' then
        return type(left) == 'number';
    end
    return left == cjson.null or left == nil
end
