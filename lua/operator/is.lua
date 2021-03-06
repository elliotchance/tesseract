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

    if right == 'null' then
        return left == cjson.null or left == nil
    end

    if right == 'array' or right == 'object' then
        return type(left) == 'table';
    end

    return no_such_type(right)
end
