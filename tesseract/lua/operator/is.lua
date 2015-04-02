local function operator_is(left, right)
    if right == 'true' then
        return left == true;
    end
    if right == 'false' then
        return left == false;
    end
    if right == 'boolean' then
        return type(left) == 'boolean';
    end
    if right == 'number' then
        return type(left) == 'number';
    end
    if right == 'string' then
        return type(left) == 'string';
    end
    return left == cjson.null or left == nil
end
