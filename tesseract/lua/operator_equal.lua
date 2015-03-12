local function operator_equal(left, right)
    -- If either value is null then the result is always null.
    if left == cjson.null or right == cjson.null then
        return cjson.null
    end

    -- Comparing arrays and objects with each other.
    if type(left) == 'table' and type(right) == 'table' then
        -- Unfortunately the only way to get the total number of items
        -- in a lua table is to physically iterate it.
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

        -- Iterate each of the left items ad verify that it exists (key
        -- and value) in the right.
        for key, value in pairs(left) do
            -- The value must be equal
            if not operator_equal(value, right[key]) then
                return false
            end
        end

        -- If it make it to here then there table contains zero elements
        -- and will always be equal
        return true
    end

    -- If the left is a boolean, but the right is some other type we
    -- swap them.
    if type(left) == 'boolean' then
        left, right = right, left
    end

    -- If only one side is a boolean it is a special comparison for
    -- truthfullness.
    if type(right) == 'boolean' then
        if type(left) == 'boolean' then
            -- do nothing
        elseif tonumber(left) ~= nil then
            left = left ~= 0
        elseif type(left) == 'table' then
            local found = false
            for _ in ipairs(left) do
                found = true
                break
            end
            left = found
        else
            left = left ~= ""
        end

        return (left == right)
    end

    -- Comparing table with non-table
    if type(left) == 'table' or type(right) == 'table' then
        return false
    end

    -- Let Lua handle converting string and numbers for value
    -- comparison.
    return tonumber(left) == tonumber(right)
end
