local function operator_concat(left, right)
    -- We do not allow arrays or objects.
    if type(left) == 'table' or type(right) == 'table' then
        no_such_operator(left, '||', right)
    end

    -- null renders to a blank string.
    if left == cjson.null then
        left = ''
    end
    if right == cjson.null then
        right = ''
    end

    -- Join strings.
    return tostring(left) .. tostring(right)
end
