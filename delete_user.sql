-- Delete user and all related records
-- Replace 'user_email@example.com' with the actual email

BEGIN;

-- Get the user ID first
DO $$
DECLARE
    user_id_to_delete VARCHAR(36);
BEGIN
    -- Replace with the actual email
    SELECT id INTO user_id_to_delete FROM mall_customuser WHERE email = 'user_email@example.com';
    
    IF user_id_to_delete IS NOT NULL THEN
        -- Delete from AdminAuditLog
        DELETE FROM mall_adminauditlog WHERE admin_user_id = user_id_to_delete;
        
        -- Delete from AdminUserRole
        DELETE FROM mall_adminuserrole WHERE user_id = user_id_to_delete;
        DELETE FROM mall_adminuserrole WHERE assigned_by_id = user_id_to_delete;
        
        -- Delete from AdminCustomPermission
        DELETE FROM mall_admincustompermission WHERE user_id = user_id_to_delete;
        DELETE FROM mall_admincustompermission WHERE assigned_by_id = user_id_to_delete;
        
        -- Delete products created by this user
        DELETE FROM mall_product WHERE created_by_id = user_id_to_delete;
        
        -- Finally delete the user
        DELETE FROM mall_customuser WHERE id = user_id_to_delete;
        
        RAISE NOTICE 'User deleted successfully';
    ELSE
        RAISE NOTICE 'User not found';
    END IF;
END $$;

COMMIT;
