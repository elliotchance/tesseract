local function operator_not_in(left, right)
    -- If the value is null then the result is always null.
    if left == cjson.null then
        return cjson.null
    end

    -- We must check for any `null` value before testing for equality.
    for key in pairs(right) do
        -- If any of the values are null we can end here.
        if right[key] == cjson.null then
            return cjson.null
        end
    end

    -- All the values are known, try to find the value in the set.
    for key in pairs(right) do
        -- Do crash-safe comparison.
        if operator_equal(right[key], left, false) then
            return false
        end
    end

    -- We must conclude that the value was not in the set.
    return true
end
