SELECT 
    t.serial,
    t.created_at AS transaction_created_at, 
    u.full_name,
    u.phone_number,
    u.email, 
    c.title,
    cat.name AS category_name,
    v.code, 
    c.price_normal,
    MIN(cup.created_at) AS progress_created_at, 
    MAX(cup.updated_at) AS progress_updated_at,
    MAX(cup.progress_percentage) AS progress,
    cq.total_correct_answers
FROM 
    transactions t
LEFT JOIN 
    users u ON t.user_serial = u.serial 
LEFT JOIN 
    courses c ON t.course_serial = c.serial 
LEFT JOIN 
    vouchers v ON t.voucher_serial = v.serial 
LEFT JOIN 
    voucher_claims vc ON vc.user_serial = u.serial AND vc.voucher_serial = v.serial 
LEFT JOIN 
    categories cat ON c.category_serial = cat.serial 
LEFT JOIN 
    course_users cu ON t.course_serial = cu.course_serial AND t.user_serial = cu.user_serial 
LEFT JOIN 
    course_user_progress cup ON cu.course_serial = cup.course_serial AND cu.user_serial = cup.user_serial 
LEFT JOIN 
    course_sections cs ON c.serial = cs.course_serial 
LEFT JOIN 
    course_contents cc ON c.serial = cc.course_serial 
LEFT JOIN 
    (
        SELECT 
            cuqa.user_serial, 
            cuqa.course_serial, 
            SUM(cuqa.is_correct) AS total_correct_answers
        FROM 
            course_user_quiz_answers cuqa
        GROUP BY 
            cuqa.user_serial, cuqa.course_serial
    ) cq 
    ON u.serial = cq.user_serial AND c.serial = cq.course_serial
WHERE 
    t.status = 'SUCCEEDED'
    AND t.invoice_id IS NOT NULL
    AND v.code = 'KOGNISIXBPJSTK'
GROUP BY 
    t.serial,
    t.created_at, 
    u.full_name,
    u.phone_number,
    u.email, 
    c.title,
    cat.name,
    v.code, 
    c.price_normal,
    cq.total_correct_answers;
