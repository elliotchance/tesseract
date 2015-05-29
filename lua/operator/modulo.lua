local function operator_modulo(left, right)
    -- If either value is null then the result is always null.
    if left == nil or right == nil or
            left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- We only allow the division of numbers
    if type(left) ~= 'number' or type(right) ~= 'number' then
        no_such_operator(left, '%', right)
    end

    if right == 0 then
        error('Modulo by zero.')
    end

    return left % right
end