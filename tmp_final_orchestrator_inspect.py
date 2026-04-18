from workflows.runtime_orchestrator import runtime_orchestrator
from workflows.cross_plane_summary_pack import cross_plane_summary_pack
from workflows.cross_plane_dashboard_pack import cross_plane_dashboard_pack
from workflows.cross_plane_closure_pack import cross_plane_closure_pack
from workflows.cross_plane_status_pack import cross_plane_status_pack
from workflows.cross_plane_policy_pack import cross_plane_policy_pack
from workflows.control_plane_summary_pack import control_plane_summary_pack
from workflows.portfolio_summary_pack import portfolio_summary_pack
from tests.test_runtime_orchestrator import make_cp_sum, make_pf_sum

cp = make_cp_sum('nominal')
pf = make_pf_sum('nominal')

# Step through orchestrator logic manually
pf_sum = portfolio_summary_pack(pf)
cp_sum = control_plane_summary_pack(
    cp.get('event_control_summary_pack', {}),
    cp.get('event_dashboard_pack', {}),
    pf_sum['portfolio_summary'],
    cp.get('portfolio_dashboard_pack', {}),
    cp.get('portfolio_control_summary_pack', {}),
    cp.get('portfolio_governance_pack', {}),
    cp.get('portfolio_resolution_decision_pack', {})
)
cp_pol = {'control_plane_policy_status': cp.get('control_plane_policy_status', 'ready')}
pf_pol = {'portfolio_policy_decision': cp.get('portfolio_policy_decision', 'proceed_policy')}
cp_stat = {'control_plane_status': cp.get('control_plane_status', 'nominal')}
pf_stat = {'portfolio_status': cp.get('portfolio_status', 'nominal')}
cp_clo = {'control_plane_closure': cp.get('control_plane_closure', 'closure_ready')}
pf_clo = {'portfolio_closure': cp.get('portfolio_closure', 'closure_ready')}
cp_dash = {'control_plane_dashboard': cp.get('control_plane_dashboard', 'nominal')}
pf_dash = {'portfolio_dashboard': cp.get('portfolio_dashboard', 'nominal')}

cross_pol = cross_plane_policy_pack(cp_pol, pf_pol, cp_sum, pf_sum, cp_dash, pf_dash, cp_clo, pf_clo, cp_stat, pf_stat)
print('CROSS_PLANE_POLICY:', cross_pol)
cross_stat = cross_plane_status_pack(cp_stat, pf_stat, cross_pol, cp_pol, pf_pol, cp_sum, pf_sum, cp_dash, pf_dash, cp_clo, pf_clo)
print('CROSS_PLANE_STATUS:', cross_stat)
cross_clo = cross_plane_closure_pack(cp_clo, pf_clo, cross_stat, cross_pol, cp_stat, pf_stat, cp_pol, pf_pol, cp_sum, pf_sum, cp_dash, pf_dash)
print('CROSS_PLANE_CLOSURE:', cross_clo)
cross_dash = cross_plane_dashboard_pack(cp_dash, pf_dash, cross_clo, cross_stat, cross_pol, cp_sum, pf_sum, cp_clo, pf_clo, cp_stat, pf_stat, cp_pol, pf_pol)
print('CROSS_PLANE_DASHBOARD:', cross_dash)

print('CROSS_PLANE_SUMMARY_PACK INPUTS:')
print('  cp_sum:', cp_sum)
print('  pf_sum:', pf_sum)
print('  cross_dash:', cross_dash)
print('  cross_clo:', cross_clo)
print('  cross_stat:', cross_stat)
print('  cross_pol:', cross_pol)

cross_sum = cross_plane_summary_pack(cp_sum, pf_sum, cross_dash, cross_clo, cross_stat, cross_pol, cp_dash, pf_dash, cp_clo, pf_clo, cp_stat, pf_stat, cp_pol, pf_pol)
print('CROSS_PLANE_SUMMARY_PACK OUTPUT:', cross_sum)
