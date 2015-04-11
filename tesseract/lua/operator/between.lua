local function operator_between(left, right)
    -- If the value is null then the result is always null.
    if left == cjson.null or right[1] == cjson.null
        or right[2] == cjson.null then
        return cjson.null
    end

    return left >= right[1] and left <= right[2]
end
