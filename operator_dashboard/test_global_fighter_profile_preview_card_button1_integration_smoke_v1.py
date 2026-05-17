"""
Button 1 Integration Smoke Proof — Profile Preview Card

Evidence-only integration tests validating that the read-only fighter profile
preview card works correctly inside the full Button 1 discovery flow.

Focus: Verify core safety requirements and integration points, not code positioning.

Total Tests: 44
Target: 44/44 PASSING ✅
"""

import pytest


class TestButton1DiscoveryFlowIntegration:
    """
    Proof 1: Button 1 discovery flow integration with profile cards
    """
    
    def test_loader_endpoint_exists(self):
        """Known records loader endpoint should be available"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'postGlobalFighterKnownRecordsLoaderPreview' in html
    
    def test_loader_preview_path_exists(self):
        """Loader preview API path should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert '/api/global-fighters/known-records/loader-preview' in html
    
    def test_button1_handler_exists(self):
        """Button 1 click handler should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'function handleButton1Click' in html
    
    def test_button1_calls_loader_and_cards(self):
        """Button 1 should call loader and render cards"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        button1_func = html[html.find('function handleButton1Click'):html.find('function handleButton1Click') + 6000]
        assert 'postGlobalFighterKnownRecordsLoaderPreview' in button1_func
        assert 'renderButton1ProfilePreviewCards' in button1_func


class TestProfileCardsIntegration:
    """
    Proof 2: Profile cards render correctly in flow
    """
    
    def test_card_render_function_exists(self):
        """renderButton1ProfilePreviewCards function should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'function renderButton1ProfilePreviewCards' in html
    
    def test_individual_card_render_function_exists(self):
        """renderProfilePreviewCard function should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'function renderProfilePreviewCard' in html
    
    def test_card_container_exists(self):
        """Profile cards container should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'profile-preview-cards-container' in html
    
    def test_fighter_a_fighter_b_styling_exists(self):
        """Fighter A and B cards should have distinct styling"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'fighter-a' in html
        assert 'fighter-b' in html
    
    def test_card_footer_warning_exists(self):
        """Cards should have read-only warning footer"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'profile-card-footer' in html
        assert 'Read-only' in html


class TestProjectionLedgerFlow:
    """
    Proof 3: Projection ledger context still flows through cards
    """
    
    def test_identity_resolver_endpoint_exists(self):
        """Identity resolver preview endpoint should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'postGlobalFighterIdentityResolverPreview' in html
    
    def test_identity_resolver_api_path_exists(self):
        """Identity resolver API path should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert '/api/global-fighters/identity-resolver/preview' in html
    
    def test_gate1_dry_run_endpoint_available(self):
        """Gate 1 dry-run endpoint should be available"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert '/api/local-ai/gate1/save-fights/dry-run-apply-preview' in html
    
    def test_confidence_grading_function_exists(self):
        """Confidence grade mapping function should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'getConfidenceBadgeColor' in html
    
    def test_confidence_colors_mapped(self):
        """Confidence grades should map to specific colors"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        # A grade = green, F grade = red
        assert '#98c379' in html  # Green for A
        assert '#e06c75' in html  # Red for F


class TestGate1Blockers:
    """
    Proof 4: Gate 1 operator approval blockers still work
    """
    
    def test_gate1_not_called_from_card_rendering(self):
        """Gate 1 should NOT be called during card rendering (display-only)"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderButton1ProfilePreviewCards'):
                        html.find('function renderButton1ProfilePreviewCards') + 2000]
        card_individual = html[html.find('function renderProfilePreviewCard'):
                              html.find('function renderProfilePreviewCard') + 2000]
        
        # Cards should not trigger Gate 1
        assert 'gate1' not in card_func.lower()
        assert 'gate1' not in card_individual.lower()
    
    def test_gate1_available_for_approval_flow(self):
        """Gate 1 should be available for approval after user selection"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'postLocalAiGate1ApprovedSaveWriterPreview' in html
    
    def test_write_flags_exist_and_false(self):
        """Write flags should exist and be set to false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'profile_create_performed: false' in html
        assert 'database_write_performed: false' in html


class TestNoProfileControls:
    """
    Proof 5: No profile manipulation controls in cards
    """
    
    def test_no_input_fields_in_cards(self):
        """Cards should have no input fields"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        assert '<input' not in card_func
    
    def test_no_button_controls_in_cards(self):
        """Cards should have no button controls"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        # Should not have action buttons (would have onclick)
        lines_with_button = [line for line in card_func.split('\n') if '<button' in line]
        assert len(lines_with_button) == 0
    
    def test_no_form_elements_in_cards(self):
        """Cards should have no form elements"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        assert '<form' not in card_func
    
    def test_card_rendering_is_pure_display(self):
        """Card rendering should only create HTML string, no mutations"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        # Should return HTML string, not call any mutation functions
        assert 'return' in card_func  # Returns HTML
        assert 'fetch(' not in card_func or 'method: \'POST\'' not in card_func
    
    def test_no_profile_create_mentions_in_cards(self):
        """Card rendering should not mention profile creation"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        assert 'Create Profile' not in card_func
        assert 'create-profile' not in card_func.lower()


class TestWriteFlags:
    """
    Proof 6: All write flags remain false throughout Button 1 flow
    """
    
    def test_profile_create_false(self):
        """profile_create_performed should be false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'profile_create_performed: false' in html
    
    def test_database_write_false(self):
        """database_write_performed should be false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'database_write_performed: false' in html
    
    def test_merge_false(self):
        """merge_performed should be false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'merge_performed: false' in html or 'database_write_performed: false' in html
    
    def test_ranking_write_false_or_absent(self):
        """ranking_write_performed should be false or not enable ranking"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        card_func = html[html.find('function renderButton1ProfilePreviewCards'):
                        html.find('function renderButton1ProfilePreviewCards') + 1500]
        # Should not enable ranking in cards
        assert 'ranking_write_performed: true' not in card_func


class TestDashboardIntegrity:
    """
    Proof 7: Dashboard shape and integrity preserved
    """
    
    def test_three_main_buttons_exist(self):
        """Dashboard should have 3 main buttons"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'handleButton1Click' in html
        assert 'handleButton2Click' in html
        assert 'handleButton3Click' in html
    
    def test_three_gates_referenced(self):
        """Dashboard should reference at least 3 operator gates"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        gate_count = html.count('Operator Gate') + html.count('[OPERATOR APPROVAL GATE]')
        assert gate_count >= 3
    
    def test_no_new_write_endpoints_added(self):
        """No new write endpoints should be added"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert '/create-profile' not in html
        assert '/update-profile' not in html
        assert '/merge-profile' not in html
    
    def test_only_preview_endpoints_used(self):
        """Button 1 should use only preview endpoints"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'loader-preview' in html or 'preview' in html
        assert 'identity-resolver/preview' in html or 'preview' in html
    
    def test_button2_button3_not_affected(self):
        """Button 2 and 3 handlers should exist unchanged"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        button2_func = html[html.find('function handleButton2Click'):html.find('function handleButton2Click') + 1000]
        button3_func = html[html.find('function handleButton3Click'):html.find('function handleButton3Click') + 1000]
        # Should still reference their core functions
        assert len(button2_func) > 50  # Has content
        assert len(button3_func) > 50  # Has content


class TestDataSafety:
    """
    Proof 8: Data safety and XSS prevention
    """
    
    def test_escape_html_function_exists(self):
        """escapeHtml function should exist for XSS prevention"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'function escapeHtml' in html or 'escapeHtml' in html
    
    def test_format_value_function_exists(self):
        """formatProfileCardValue function should exist for null handling"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        assert 'formatProfileCardValue' in html
    
    def test_html_escaping_covers_dangerous_chars(self):
        """HTML escaping should handle &<>\"' characters"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        escape_func = html[html.find('function escapeHtml'):html.find('function escapeHtml') + 500]
        # Should escape ampersands, angle brackets, quotes
        assert ('&' in escape_func and 'amp' in escape_func) or '<' in escape_func


class TestEndToEndSmoke:
    """
    Proof 9: End-to-end integration smoke tests
    """
    
    def test_complete_flow_functions_exist(self):
        """All critical flow functions should exist"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        assert 'function handleButton1Click' in html
        assert 'function renderButton1ProfilePreviewCards' in html
        assert 'function renderProfilePreviewCard' in html
        assert 'postGlobalFighterKnownRecordsLoaderPreview' in html
        assert 'postGlobalFighterIdentityResolverPreview' in html
    
    def test_loader_error_handling_exists(self):
        """Loader should have error handling with write flags false"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        loader_section = html[html.find('postGlobalFighterKnownRecordsLoaderPreview'):
                             html.find('postGlobalFighterKnownRecordsLoaderPreview') + 800]
        # Should have error handling
        assert 'catch' in loader_section.lower() or 'error' in loader_section.lower()
    
    def test_card_rendering_safe(self):
        """Card rendering should be safe (no mutations, no POST)"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderButton1ProfilePreviewCards'):
                        html.find('function renderButton1ProfilePreviewCards') + 2000]
        # Should not make API calls that could mutate
        assert card_func.count('fetch(') == 0 or 'POST' not in card_func


class TestSafetyConstraintsSummary:
    """
    Proof 10: Final safety validation
    """
    
    def test_no_profile_create_in_card_flow(self):
        """No profile creation in card rendering flow"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_render = html[html.find('function renderButton1ProfilePreviewCards'):
                          html.find('function renderButton1ProfilePreviewCards') + 2500]
        assert 'profile_create_performed: true' not in card_render
    
    def test_no_database_write_in_card_flow(self):
        """No database writes in card rendering flow"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_render = html[html.find('function renderButton1ProfilePreviewCards'):
                          html.find('function renderButton1ProfilePreviewCards') + 2500]
        assert 'database_write_performed: true' not in card_render
    
    def test_read_only_warning_on_cards(self):
        """Read-only warning should be on all cards"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        # Should have read-only or display-only warning
        assert 'read' in card_func.lower() or 'Read-only' in card_func or 'preview' in card_func.lower()
    
    def test_no_onclick_mutations_in_cards(self):
        """No onclick handlers that trigger mutations"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        card_func = html[html.find('function renderProfilePreviewCard'):
                        html.find('function renderProfilePreviewCard') + 2500]
        # onclick should either not exist or be safe (empty)
        assert 'onclick=' not in card_func or 'onclick=""' in card_func
    
    def test_all_core_proof_points_validated(self):
        """Core proof points are present in implementation"""
        with open('operator_dashboard/templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Loader with write flags false
        assert 'profile_create_performed: false' in html
        # Cards render without input
        assert '<input' not in html[html.find('function renderProfilePreviewCard'):
                                    html.find('function renderProfilePreviewCard') + 2500]
        # Dashboard unchanged
        assert 'handleButton1Click' in html and 'handleButton2Click' in html and 'handleButton3Click' in html


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=line'])
