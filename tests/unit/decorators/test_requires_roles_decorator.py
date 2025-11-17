from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.common.decorators.requires_all_roles import requires_all_roles
from app.common.view_models import AuthRole


class TestRequiresRolesDecorator(IsolatedAsyncioTestCase):

    @pytest.mark.asyncio
    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_has_required_roles_all(self, get_user_roles):
        # Arrange
        get_user_roles.return_value = [AuthRole.REPORTING_API, AuthRole.ADVERTISER_API]

        @requires_all_roles([AuthRole.ADVERTISER_API, AuthRole.REPORTING_API])
        async def test_function():
            return 'Has required roles all'

        # Act
        result = await test_function()

        # Assert
        self.assertEqual(result, 'Has required roles all')

    @pytest.mark.asyncio
    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_has_required_roles(self, get_user_roles):
        # Arrange
        get_user_roles.return_value = [AuthRole.REPORTING_API, AuthRole.ADVERTISER_API]

        @requires_all_roles([AuthRole.REPORTING_API])
        async def test_function():
            return 'Has required roles'

        # Act
        result = await test_function()

        # Assert
        self.assertEqual(result, 'Has required roles')

    @pytest.mark.asyncio
    @patch('app.common.decorators.requires_all_roles.EntClientServiceGateway.get_user_roles')
    async def test_does_not_have_required_roles(self, get_user_roles):
        # Arrange
        get_user_roles.return_value = [AuthRole.ADVERTISER_API]

        @requires_all_roles([AuthRole.REPORTING_API])
        async def test_function():
            return 'Has required roles'

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            await test_function()

        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Missing authorization roles to perform this operation. Please contact support.")