# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Stephanie Federwisch'

from core.domain import collection_services
from core.domain import exp_services
from core.domain import rights_manager
from core.domain import user_services
from core.tests import test_utils
import feconf
import utils


class UserServicesUnitTests(test_utils.GenericTestBase):
    """Test the user services methods."""

    def test_set_and_get_username(self):
        user_id = 'someUser'
        username = 'username'
        with self.assertRaisesRegexp(Exception, 'User not found.'):
            user_services.set_username(user_id, username)

        user_services._create_user(user_id, 'email@email.com')

        user_services.set_username(user_id, username)
        self.assertEquals(username, user_services.get_username(user_id))

    def test_get_username_for_nonexistent_user(self):
        with self.assertRaisesRegexp(Exception, 'User not found.'):
            user_services.get_username('fakeUser')

    def test_get_username_none(self):
        user_services._create_user('fakeUser', 'email@email.com')
        self.assertEquals(None, user_services.get_username('fakeUser'))

    def test_is_username_taken_false(self):
        self.assertFalse(user_services.is_username_taken('fakeUsername'))

    def test_is_username_taken_true(self):
        user_id = 'someUser'
        username = 'newUsername'
        user_services._create_user(user_id, 'email@email.com')
        user_services.set_username(user_id, username)
        self.assertTrue(user_services.is_username_taken(username))

    def test_is_username_taken_different_case(self):
        user_id = 'someUser'
        username = 'camelCase'
        user_services._create_user(user_id, 'email@email.com')
        user_services.set_username(user_id, username)
        self.assertTrue(user_services.is_username_taken('CaMeLcAsE'))

    def test_set_invalid_usernames(self):
        user_id = 'someUser'
        user_services._create_user(user_id, 'email@email.com')
        bad_usernames = [
            ' bob ', '@', '', 'a' * 100, 'ADMIN', 'admin', 'AdMiN2020']
        for username in bad_usernames:
            with self.assertRaises(utils.ValidationError):
                user_services.set_username(user_id, username)

    def test_invalid_emails(self):
        bad_email_addresses = ['@', '@@', 'abc', '', None, ['a', '@', 'b.com']]
        for email in bad_email_addresses:
            with self.assertRaises(utils.ValidationError):
                user_services.get_or_create_user('user_id', email)

    def test_email_truncation(self):
        email_addresses = [
            ('a@b.c', '..@b.c'),
            ('ab@c.d', 'a..@c.d'),
            ('abc@def.gh', 'a..@def.gh'),
            ('abcd@efg.h', 'a..@efg.h'),
            ('abcdefgh@efg.h', 'abcde..@efg.h'),
        ]
        for ind, (actual_email, expected_email) in enumerate(email_addresses):
            user_settings = user_services.get_or_create_user(
                str(ind), actual_email)
            self.assertEqual(user_settings.truncated_email, expected_email)

    def test_get_email_from_username(self):
        user_id = 'someUser'
        username = 'username'
        user_email = 'email@email.com'

        user_services._create_user(user_id, user_email)
        user_services.set_username(user_id, username)
        self.assertEquals(user_services.get_username(user_id), username)

        # Handle usernames that exist.
        self.assertEquals(
            user_services.get_email_from_username(username), user_email)

        # Handle usernames in the same equivalence class correctly.
        self.assertEquals(
            user_services.get_email_from_username('USERNAME'), user_email)

        # Return None for usernames which don't exist.
        self.assertIsNone(
            user_services.get_email_from_username('fakeUsername'))

    def test_get_user_id_from_username(self):
        user_id = 'someUser'
        username = 'username'
        user_email = 'email@email.com'

        user_services._create_user(user_id, user_email)
        user_services.set_username(user_id, username)
        self.assertEquals(user_services.get_username(user_id), username)

        # Handle usernames that exist.
        self.assertEquals(
            user_services.get_user_id_from_username(username), user_id)

        # Handle usernames in the same equivalence class correctly.
        self.assertEquals(
            user_services.get_user_id_from_username('USERNAME'), user_id)

        # Return None for usernames which don't exist.
        self.assertIsNone(
            user_services.get_user_id_from_username('fakeUsername'))


class UpdateContributionMsecTests(test_utils.GenericTestBase):
    """Test whether contribution date changes with publication of
    exploration/collection and update of already published exploration/collection
    """

    EXP_ID = 'test_exp'
    COL_ID = 'test_col'
    COLLECTION_TITLE = 'title'
    COLLECTION_CATEGORY = 'category'
    COLLECTION_OBJECTIVE = 'objective'

    def test_contribution_msec_updates_on_published_explorations(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)

        exploration = self.save_new_valid_exploration(
            self.EXP_ID, self.admin_id, end_state_name='End')
        self.init_state_name = exploration.init_state_name
        exp_services.publish_exploration_and_update_user_profiles(
            self.admin_id, self.EXP_ID)

        # Test all owners and editors of exploration after publication have
        # updated first contribution times in msecs.
        self.assertIsNotNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)

        # Test editor of published exploration has updated contribution time.
        rights_manager.release_ownership_of_exploration(
            self.admin_id, self.EXP_ID)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)

        exp_services.update_exploration(
            self.editor_id, self.EXP_ID, [{
                'cmd': 'edit_state_property',
                'state_name': self.init_state_name,
                'property_name': 'widget_id',
                'new_value': 'MultipleChoiceInput'
            }], 'commit')

        self.assertIsNotNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_update_until_exploration_is_published(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)

        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)

        exploration = self.save_new_valid_exploration(
            self.EXP_ID, self.admin_id, end_state_name='End')
        self.init_state_name = exploration.init_state_name

        # Test that saving an exploration does not update first contribution
        # time.
        self.assertIsNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)

        # Test that commit to unpublished exploration does not update
        # contribution time.
        exp_services.update_exploration(
            self.admin_id, self.EXP_ID, [{
                'cmd': 'edit_state_property',
                'state_name': self.init_state_name,
                'property_name': 'widget_id',
                'new_value': 'MultipleChoiceInput'
            }], '')
        self.assertIsNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)

        # Test that another user who commits to unpublished exploration does not
        # have updated first contribution time.
        rights_manager.assign_role_for_exploration(
            self.admin_id, self.EXP_ID, self.editor_id, 'editor')
        exp_services.update_exploration(
            self.editor_id, self.EXP_ID, [{
            'cmd': 'rename_state',
            'old_state_name': feconf.DEFAULT_INIT_STATE_NAME,
            'new_state_name': u'¡Hola! αβγ',
            }], '')
        self.assertIsNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

        # Test that after an exploration is published, all contributors have
        # updated first contribution time.
        exp_services.publish_exploration_and_update_user_profiles(
            self.admin_id, self.EXP_ID)
        self.assertIsNotNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)
        self.assertIsNotNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_change_if_no_contribution_to_exploration(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)

        exploration = self.save_new_valid_exploration(
            self.EXP_ID, self.admin_id, end_state_name='End')
        rights_manager.assign_role_for_exploration(
            self.admin_id, self.EXP_ID, self.editor_id, 'editor')
        exp_services.publish_exploration_and_update_user_profiles(
            self.admin_id, self.EXP_ID)

        # Test that contribution time is not given to an editor that has not
        # contributed.
        self.assertIsNotNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)
        self.assertIsNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_change_if_exploration_unpublished(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)
        self.set_admins([self.ADMIN_EMAIL])

        self.signup(self.OWNER_EMAIL, self.OWNER_USERNAME)
        self.owner_id = self.get_user_id_from_email(self.OWNER_EMAIL)

        exploration = self.save_new_valid_exploration(
            self.EXP_ID, self.owner_id, end_state_name='End')
        self.init_state_name = exploration.init_state_name
        exp_services.publish_exploration_and_update_user_profiles(
            self.owner_id, self.EXP_ID)
        rights_manager.unpublish_exploration(self.admin_id, self.EXP_ID)

        # Test that contribution time is not eliminated if exploration is
        # unpublished.
        self.assertIsNotNone(user_services.get_user_settings(
            self.owner_id).first_contribution_msec)

    def test_contribution_msec_updates_on_published_collections(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)

        collection = self.save_new_valid_collection(
            self.COL_ID, self.admin_id, title=self.COLLECTION_TITLE,
            category=self.COLLECTION_CATEGORY,
            objective=self.COLLECTION_OBJECTIVE,
            exploration_id=self.EXP_ID)

        collection_services.publish_collection_and_update_user_profiles(
            self.admin_id, self.COL_ID)

        # Test all owners and editors of collection after publication have
        # updated first contribution times.
        self.assertIsNotNone(user_services.get_user_settings(self.admin_id)
            .first_contribution_msec)

        # Test editor of published collection has updated first contribution time.
        rights_manager.release_ownership_of_collection(self.admin_id,
            self.COL_ID)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)

        collection_services.update_collection(
            self.editor_id, self.COL_ID, [{
                'cmd': 'edit_collection_property',
                'property_name': 'title',
                'new_value': 'Some new title'
            }], 'Changed the title')

        self.assertIsNotNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_update_until_collection_is_published(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)

        collection = self.save_new_valid_collection(
            self.COL_ID, self.admin_id, title=self.COLLECTION_TITLE,
            category=self.COLLECTION_CATEGORY,
            objective=self.COLLECTION_OBJECTIVE,
            exploration_id=self.EXP_ID)

        # Test that saving a collection does not update first contribution
        # time.
        self.assertIsNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)

        # Test that commit to unpublished collection does not update
        # contribution time.
        collection_services.update_collection(
            self.admin_id, self.COL_ID, [{
                'cmd': 'edit_collection_property',
                'property_name': 'title',
                'new_value': 'Some new title'
            }], '')
        self.assertIsNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)

        # Test that another user who commits to unpublished collection does not
        # have updated first contribution time.
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)
        rights_manager.assign_role_for_collection(
            self.admin_id, self.COL_ID, self.editor_id, 'editor')
        collection_services.update_collection(
                self.editor_id, self.COL_ID, [{
                'cmd': 'edit_collection_property',
                'property_name': 'category',
                'new_value': 'Some new category'
            }], '')
        self.assertIsNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

        # Test that after an collection is published, all contributors have
        # updated first contribution times.
        collection_services.publish_collection_and_update_user_profiles(
            self.admin_id, self.COL_ID)
        self.assertIsNotNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)
        self.assertIsNotNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_change_if_no_contribution_to_collection(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)
        self.signup(self.EDITOR_EMAIL, self.EDITOR_USERNAME)
        self.editor_id = self.get_user_id_from_email(self.EDITOR_EMAIL)

        collection = self.save_new_valid_collection(
            self.COL_ID, self.admin_id, title=self.COLLECTION_TITLE,
            category=self.COLLECTION_CATEGORY,
            objective=self.COLLECTION_OBJECTIVE,
            exploration_id=self.EXP_ID)
        rights_manager.assign_role_for_collection(
            self.admin_id, self.COL_ID, self.editor_id, 'editor')
        collection_services.publish_collection_and_update_user_profiles(
            self.admin_id, self.COL_ID)

        # Test that contribution time is not given to an editor that has not
        # contributed.
        self.assertIsNotNone(user_services.get_user_settings(
            self.admin_id).first_contribution_msec)
        self.assertIsNone(user_services.get_user_settings(
            self.editor_id).first_contribution_msec)

    def test_contribution_msec_does_not_change_if_collection_unpublished(self):
        self.signup(self.ADMIN_EMAIL, self.ADMIN_USERNAME)
        self.admin_id = self.get_user_id_from_email(self.ADMIN_EMAIL)
        self.set_admins([self.ADMIN_EMAIL])

        self.signup(self.OWNER_EMAIL, self.OWNER_USERNAME)
        self.owner_id = self.get_user_id_from_email(self.OWNER_EMAIL)

        collection = self.save_new_valid_collection(
            self.COL_ID, self.owner_id, title=self.COLLECTION_TITLE,
            category=self.COLLECTION_CATEGORY,
            objective=self.COLLECTION_OBJECTIVE,
            exploration_id=self.EXP_ID)
        collection_services.publish_collection_and_update_user_profiles(
            self.owner_id, self.COL_ID)
        rights_manager.unpublish_collection(self.admin_id, self.COL_ID)

        # Test that first contribution msec is not eliminated if collection is
        # unpublished.
        self.assertIsNotNone(user_services.get_user_settings(
            self.owner_id).first_contribution_msec)
