local function operator_is(left, right)
    if right == 'number' then
        return true;
    end
    return left == cjson.null or left == nil
end
