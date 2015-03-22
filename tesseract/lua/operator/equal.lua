local function operator_equal(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- Comparing different types is not allowed.
    if type(left) ~= type(right) then
        no_such_operator(left, '=', right)
    end

    -- Comparing arrays and objects with each other.
    if type(left) == 'table' then
        -- Unfortunately the only way to get the total number of items in a lua
        -- table is to physically iterate it.
        local left_len = 0
        for _ in pairs(left) do
            left_len = left_len + 1
        end

        local right_len = 0
        for _ in pairs(right) do
            right_len = right_len + 1
        end

        -- Tables are not equal if they are different sizes.
        if left_len ~= right_len then
            return false
        end

        -- Iterate each of the left items ad verify that it exists (key and
        -- value) in the right.
        for key, value in pairs(left) do
            -- The value must be equal
            if not operator_equal(value, right[key]) then
                return false
            end
        end

        -- If it make it to here then there table contains zero elements and
        -- will always be equal
        return true
    end

    -- If only one side is a boolean it is a special comparison for
    -- truthfullness.
    if type(right) == 'boolean' then
        return (left == right)
    end

    -- Let Lua handle converting string and numbers for value comparison.
    return left == right
end
