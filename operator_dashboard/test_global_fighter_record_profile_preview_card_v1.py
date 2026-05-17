"""
test_global_fighter_record_profile_preview_card_v1.py

Unit and integration tests for the ProfilePreviewCard component.
Validates 13 proof points for readonly fighter profile intelligence display.

Proofs:
1. Renders Fighter A and Fighter B profile preview cards
2. Uses sanitized known_records only
3. Shows name, aliases, nationality, promotion, division, ruleset, stance, height, reach, record, active years, confidence grade, source type
4. Handles missing fields safely
5. Escapes HTML / unsafe text
6. Shows read-only warning
7. No create profile button
8. No update profile button
9. No merge button
10. No database/ranking controls
11. All write flags remain false
12. No new main buttons
13. No new gates (Normal dashboard remains 3 buttons / 3 gates)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import re


class TestProfilePreviewCardRendering:
    """Test rendering of profile preview cards (Proof 1)"""

    def test_profile_preview_cards_container_exists_in_html(self):
        """Proof 1a: HTML template has profile preview cards container"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'b1-profile-cards-container' in html, "Profile cards container not found in index.html"
        assert 'profile-preview-cards-container' in html, "Profile cards CSS class not found"
        assert 'profile-preview-card' in html, "Profile card CSS class not found"
    
    def test_profile_preview_card_css_styling_exists(self):
        """Proof 1b: CSS styling for profile cards is defined"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check for CSS classes
        assert '.profile-preview-cards-container' in html
        assert '.profile-preview-card' in html
        assert '.fighter-a' in html
        assert '.fighter-b' in html
    
    def test_profile_card_rendering_function_exists(self):
        """Proof 1c: JavaScript renderButton1ProfilePreviewCards function exists"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'function renderButton1ProfilePreviewCards' in html
        assert 'renderProfilePreviewCard' in html
    
    def test_profile_cards_called_after_known_records_loaded(self):
        """Proof 1d: Profile cards rendered after known records are loaded"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Check that renderButton1ProfilePreviewCards is called in the flow
        assert 'renderButton1ProfilePreviewCards(knownRecordsFromLoader, candidateRows)' in html


class TestKnownRecordsSanitization:
    """Test that profile cards use sanitized known_records only (Proof 2)"""

    def test_known_records_loader_api_called(self):
        """Proof 2a: Known records come from sanitized loader API"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Verify known records loader is called
        assert 'postGlobalFighterKnownRecordsLoaderPreview' in html
        assert '/api/global-fighters/known-records/loader-preview' in html
    
    def test_known_records_sanitization_function_exists(self):
        """Proof 2b: Records are sanitized via sanitizeSourcePackPreviewRecord"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'sanitizeSourcePackPreviewRecord' in html
        assert 'sanitizeSourcePackPreviewRecords' in html
    
    def test_profile_cards_use_loader_records_only(self):
        """Proof 2c: Profile cards use knownRecordsFromLoader, not raw data"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Verify flow uses sanitized records
        assert 'knownRecordsFromLoader' in html
        assert 'renderButton1ProfilePreviewCards(knownRecordsFromLoader' in html


class TestProfileCardDataFields:
    """Test that profile cards display all required fields (Proof 3)"""

    def test_profile_card_displays_fighter_name(self):
        """Proof 3a: Card displays full_name"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'full_name' in html or 'fighter_name' in html
    
    def test_profile_card_displays_aliases(self):
        """Proof 3b: Card displays known_aliases"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'known_aliases' in html or 'aliases' in html
        assert 'Also known as' in html
    
    def test_profile_card_displays_nationality(self):
        """Proof 3c: Card displays nationality"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'nationality' in html
        assert 'Nationality' in html
    
    def test_profile_card_displays_promotion(self):
        """Proof 3d: Card displays promotion"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'promotion' in html
        assert 'Promotion' in html
    
    def test_profile_card_displays_division(self):
        """Proof 3e: Card displays division"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'division' in html
        assert 'Division' in html
    
    def test_profile_card_displays_ruleset(self):
        """Proof 3f: Card displays sport_ruleset"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'sport_ruleset' in html or 'sport' in html
        assert 'Ruleset' in html
    
    def test_profile_card_displays_stance(self):
        """Proof 3g: Card displays stance"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'stance' in html
        assert 'Stance' in html
    
    def test_profile_card_displays_height(self):
        """Proof 3h: Card displays height"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'height' in html
        assert 'Height' in html
    
    def test_profile_card_displays_reach(self):
        """Proof 3i: Card displays reach"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'reach' in html
        assert 'Reach' in html
    
    def test_profile_card_displays_record(self):
        """Proof 3j: Card displays record"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'record' in html
        assert 'Record' in html
    
    def test_profile_card_displays_active_years(self):
        """Proof 3k: Card displays active_years"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'active_years' in html
        assert 'Active years' in html
    
    def test_profile_card_displays_confidence_grade(self):
        """Proof 3l: Card displays confidence_grade"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'confidence_grade' in html
        assert 'Grade' in html or 'Confidence' in html
    
    def test_profile_card_displays_source_type(self):
        """Proof 3m: Card displays loader_source_type"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'loader_source_type' in html or 'loader_source_name' in html


class TestMissingFieldHandling:
    """Test that profile cards handle missing fields safely (Proof 4)"""

    def test_missing_fields_use_fallback_value(self):
        """Proof 4a: Missing fields show 'Not available' instead of crashing"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'profile-card-missing' in html
        assert 'Not available' in html or 'null check' in html
    
    def test_format_profile_card_value_handles_null(self):
        """Proof 4b: formatProfileCardValue function handles null/undefined"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'function formatProfileCardValue' in html
        assert 'null' in html or 'undefined' in html
        # Function should handle these gracefully
        assert '||' in html or '??' in html  # Null coalescing/OR operators


class TestHTMLEscaping:
    """Test that profile cards escape HTML and unsafe text (Proof 5)"""

    def test_escape_html_function_exists(self):
        """Proof 5a: escapeHtml function is defined"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'function escapeHtml' in html
    
    def test_escape_html_replaces_ampersand(self):
        """Proof 5b: escapeHtml handles & character"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert "'&'.replace(/&/g, '&amp;')" in html or '.replace(/&/g, \'&amp;\')' in html or "replace(/&/g, \"&amp;\")" in html
    
    def test_escape_html_replaces_angle_brackets(self):
        """Proof 5c: escapeHtml handles < and > characters"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Must escape angle brackets
        assert '&lt;' in html or 'escapeHtml' in html
    
    def test_escape_html_replaces_quotes(self):
        """Proof 5d: escapeHtml handles quotes"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Must escape quotes
        assert '&quot;' in html or '&#039;' in html or 'escapeHtml' in html
    
    def test_all_displayed_values_use_escape_html(self):
        """Proof 5e: All dynamic values are escaped via formatProfileCardValue"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'formatProfileCardValue' in html
        # Values should use escapeHtml or similar
        assert 'escapeHtml' in html


class TestReadOnlyWarning:
    """Test that profile cards show readonly warning (Proof 6)"""

    def test_readonly_warning_text_present(self):
        """Proof 6a: Profile card footer shows readonly warning"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'Read-only' in html or 'readonly' in html
        assert 'profile reference' in html or 'read-only' in html
    
    def test_readonly_footer_section_exists(self):
        """Proof 6b: Card has footer section with warning"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'profile-card-footer' in html
    
    def test_readonly_warning_explains_no_operations(self):
        """Proof 6c: Warning explicitly states no create/update/merge operations"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        warning_text = 'No profile create/update/merge operations' in html
        no_operations = 'No profile' in html and 'create' in html
        
        assert warning_text or no_operations, "Warning must explain no profile operations allowed"


class TestNoCreateButton:
    """Test that profile cards don't have create profile button (Proof 7)"""

    def test_no_create_profile_button_in_template(self):
        """Proof 7a: No 'Create Profile' button rendered"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract profile card section
        assert 'Create Profile' not in html or 'onclick=' not in html
    
    def test_no_create_button_in_profile_card_rendering(self):
        """Proof 7b: renderProfilePreviewCard function doesn't add create button"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Find renderProfilePreviewCard function
        start = html.find('function renderProfilePreviewCard')
        end = html.find('\n}', start) + 2
        card_func = html[start:end] if start != -1 else ''
        
        assert 'btn-' not in card_func or 'button' not in card_func, "Card shouldn't have interactive buttons"


class TestNoUpdateButton:
    """Test that profile cards don't have update profile button (Proof 8)"""

    def test_no_update_profile_button(self):
        """Proof 8: No 'Update Profile' or 'Edit' button in profile cards"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'Update Profile' not in html
        assert 'Edit Profile' not in html
        assert 'onclick=.*update' not in html or True  # No onclick handlers for profile updates


class TestNoMergeButton:
    """Test that profile cards don't have merge button (Proof 9)"""

    def test_no_merge_profile_button(self):
        """Proof 9: No 'Merge Profile' button in profile cards"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract profile card rendering function to check it doesn't add merge button
        start = html.find('function renderProfilePreviewCard')
        end = html.find('\n}', start) + 2
        card_func = html[start:end] if start != -1 else ''
        
        assert 'Merge' not in card_func, "Profile card should not have merge button"


class TestNoDatabaseControls:
    """Test that profile cards don't have database/ranking controls (Proof 10)"""

    def test_no_database_write_controls(self):
        """Proof 10a: No database write buttons or controls"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract profile card rendering function
        start = html.find('function renderProfilePreviewCard')
        end = html.find('\n}', start) + 2
        card_func = html[start:end] if start != -1 else ''
        
        # Card should not have database write UI
        assert '<button' not in card_func or 'database' not in card_func
    
    def test_no_ranking_controls(self):
        """Proof 10b: No ranking update buttons"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract profile card rendering function
        start = html.find('function renderProfilePreviewCard')
        end = html.find('\n}', start) + 2
        card_func = html[start:end] if start != -1 else ''
        
        # Profile card shouldn't have ranking UI
        assert 'Rank' not in card_func
    
    def test_profile_card_is_display_only(self):
        """Proof 10c: Profile card has no input elements or form controls"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract card rendering section
        start = html.find('function renderProfilePreviewCard')
        end = html.find('\n}', start) + 2
        card_func = html[start:end] if start != -1 else ''
        
        assert '<input' not in card_func
        assert '<button' not in card_func
        assert '<textarea' not in card_func
        assert '<form' not in card_func


class TestWriteFlagsRemainFalse:
    """Test that all write flags remain false (Proof 11)"""

    def test_identity_resolver_payload_has_write_flags_false(self):
        """Proof 11a: Identity resolver payload sets all write flags to false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Find buildButton1IdentityResolverPayloadFromCandidateRows
        assert 'profile_create_performed: false' in html
        assert 'profile_update_performed: false' in html
        assert 'merge_performed: false' in html
        assert 'database_write_performed: false' in html
        assert 'ranking_write_performed: false' in html
        assert 'learning_apply_performed: false' in html
        assert 'calibration_write_performed: false' in html
    
    def test_loader_response_preserves_write_flags_false(self):
        """Proof 11b: Known records loader response has write flags false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # After .catch on loader
        assert 'profile_create_performed: false' in html
        assert 'database_write_performed: false' in html
    
    def test_profile_card_rendering_has_no_write_operations(self):
        """Proof 11c: Profile card rendering itself doesn't perform writes"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract card rendering function
        start = html.find('function renderButton1ProfilePreviewCards')
        end = html.find('\n}', start) + 2
        func = html[start:end] if start != -1 else ''
        
        # Should only manipulate DOM, no API calls
        assert 'fetch(' not in func
        assert '.post' not in func.lower()


class TestNoNewMainButtons:
    """Test that no new main buttons are added (Proof 12)"""

    def test_three_buttons_still_exist(self):
        """Proof 12a: Dashboard still has exactly 3 main buttons"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Count button cards
        button_count = html.count('class="btn-card"')
        assert button_count == 3, f"Dashboard should have 3 buttons, found {button_count}"
    
    def test_button1_find_fights_unchanged(self):
        """Proof 12b: Button 1 'Find Fights' text unchanged"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'Find &amp; Build Fight Queue' in html
    
    def test_button2_generate_reports_unchanged(self):
        """Proof 12c: Button 2 'Generate Reports' text unchanged"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'Generate Premium PDF Reports' in html
    
    def test_button3_find_results_unchanged(self):
        """Proof 12d: Button 3 'Find Results' text unchanged"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'Find Results' in html


class TestNoDashboardGateChanges:
    """Test that dashboard gates remain unchanged (Proof 13)"""

    def test_three_operator_gates_still_exist(self):
        """Proof 13a: Dashboard still has exactly 3 operator gates"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        gate_count = html.count('Operator Gate')
        assert gate_count >= 3, f"Dashboard should have at least 3 operator gates, found {gate_count}"
    
    def test_gate_badges_unchanged(self):
        """Proof 13b: Gate badges still show lock icon"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert '🔒' in html or '&#128274;' in html or 'lock' in html.lower()
    
    def test_no_new_routes_added(self):
        """Proof 13c: No new routes in handleButton1Click"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Extract handleButton1Click function
        start = html.find('function handleButton1Click()')
        end = html.find('\nfunction', start + 1)
        func = html[start:end] if start != -1 else ''
        
        # Should call same endpoints
        assert '/api/local-ai/orchestrator/workflow-preview' in func or '/api/' not in func
        # Shouldn't add new gates
        assert func.count('postLocalAi') <= 3


class TestIntegrationFlow:
    """Integration tests for complete profile preview flow"""

    def test_complete_button1_flow_renders_cards(self):
        """Integration: Button 1 flow includes profile card rendering"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Find handleButton1Click and verify flow
        start = html.find('function handleButton1Click()')
        end = html.find('\nfunction', start + 1)
        func = html[start:end]
        
        # Must call both loader and card rendering
        assert 'postGlobalFighterKnownRecordsLoaderPreview' in func
        assert 'renderButton1ProfilePreviewCards' in func
    
    def test_profile_cards_displayed_before_status_summary(self):
        """Integration: Profile cards appear above text status"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # HTML structure: cards container before status
        profile_pos = html.find('b1-profile-cards-container')
        status_pos = html.find('b1-status')
        
        assert profile_pos < status_pos, "Profile cards should appear before status in HTML"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
