local function operator_between(left, right)
    -- If the value is null then the result is always null.
    if left == cjson.null or right[1] == cjson.null
        or right[2] == cjson.null then
        return cjson.null
    end

    -- We can only deal with numbers.
    if type(left) ~= 'number' or type(right[1]) ~= 'number'
        or type(right[2]) ~= 'number' then
        error(string.format('No such operator %s BETWEEN %s AND %s.',
            type(left), type(right[1]), type(right[2])))
    end

    -- Perform comparison.
    return left >= right[1] and left <= right[2]
end
