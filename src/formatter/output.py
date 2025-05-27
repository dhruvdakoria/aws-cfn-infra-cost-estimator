from typing import List, Dict, Any
from tabulate import tabulate
from cost_estimator.core import ResourceCost
from stack_analyzer.diff import ResourceDiff

class CostReportFormatter:
    """Formats cost estimation results into markdown reports."""
    
    @staticmethod
    def format_cost_summary(resource_costs: List[ResourceCost]) -> str:
        """Format a summary of resource costs into a readable table."""
        if not resource_costs:
            return "📋 No resources to display."
        
        # Calculate totals
        total_hourly = sum(rc.hourly_cost for rc in resource_costs if rc.pricing_model != "usage_based")
        total_monthly = sum(rc.monthly_cost for rc in resource_costs if rc.pricing_model != "usage_based")
        currency = resource_costs[0].currency if resource_costs else "USD"
        
        # Count resources by type
        usage_based_count = len([rc for rc in resource_costs if rc.pricing_model == "usage_based"])
        free_count = len([rc for rc in resource_costs if rc.pricing_model == "free"])
        paid_count = len([rc for rc in resource_costs if rc.pricing_model not in ["free", "usage_based"] and rc.monthly_cost > 0])
        
        # Create table data with Infracost-style formatting
        table_data = []
        
        # Sort resources: paid first, then usage-based, then free
        sorted_costs = sorted(resource_costs, key=lambda x: (
            0 if x.pricing_model not in ["free", "usage_based"] and x.monthly_cost > 0 else
            1 if x.pricing_model == "usage_based" else
            2 if x.pricing_model == "free" else
            3
        ))
        
        for rc in sorted_costs:
            # Format resource type (remove AWS:: prefix)
            resource_type = rc.resource_type.replace("AWS::", "").replace("::", ":")
            
            # Handle tiered pricing resources with sub-breakdown
            if rc.usage_type == "tiered_pricing" and rc.metadata and rc.metadata.get("tier_breakdown"):
                tier_breakdown = rc.metadata["tier_breakdown"]
                
                # Main resource row
                table_data.append([
                    f"📊 {resource_type}",
                    rc.resource_id[:15] + "..." if len(rc.resource_id) > 15 else rc.resource_id,
                    "Usage-based",
                    "Monthly cost depends on usage"
                ])
                
                # Add tier sub-rows (like Infracost does)
                for tier in tier_breakdown["tiers"][:3]:  # Show first 3 tiers
                    table_data.append([
                        f"├─ {tier['description']}",
                        "",
                        tier['price'],
                        "Monthly cost depends on usage"
                    ])
                
                if tier_breakdown["total_tiers"] > 3:
                    table_data.append([
                        f"└─ ... and {tier_breakdown['total_tiers'] - 3} more tiers",
                        "",
                        "Varies",
                        "See detailed breakdown below"
                    ])
                
            else:
                # Regular resource formatting
                if rc.pricing_model == "free":
                    emoji = "🆓"
                    cost_display = "Free"
                    pricing_info = "This resource is free to use"
                elif rc.pricing_model == "usage_based":
                    emoji = "📊"
                    cost_display = "Usage-based"
                    pricing_info = rc.pricing_details[:60] + "..." if rc.pricing_details and len(rc.pricing_details) > 60 else rc.pricing_details or "Pay per use"
                elif rc.monthly_cost > 0:
                    emoji = "💰"
                    cost_display = f"${rc.monthly_cost:.2f}/month"
                    pricing_info = rc.pricing_details[:60] + "..." if rc.pricing_details and len(rc.pricing_details) > 60 else rc.pricing_details or "Fixed monthly cost"
                else:
                    emoji = "❓"
                    cost_display = "Unknown"
                    pricing_info = "Pricing information not available"
                
                table_data.append([
                    f"{emoji} {resource_type}",
                    rc.resource_id[:15] + "..." if len(rc.resource_id) > 15 else rc.resource_id,
                    cost_display,
                    pricing_info
                ])
        
        headers = ["🏗️ Resource Type", "🆔 ID", "📅 Monthly Cost", "💡 Pricing Info"]
        
        table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left", maxcolwidths=[None, None, None, 60])
        
        # Add summary section
        summary_lines = []
        summary_lines.append(f"💰 **Fixed Monthly Cost**: ${total_monthly:.2f}")
        summary_lines.append(f"⏰ **Fixed Hourly Cost**: ${total_hourly:.4f}")
        summary_lines.append(f"📊 **Usage-Based Resources**: {usage_based_count} (costs depend on usage)")
        summary_lines.append(f"🆓 **Free Resources**: {free_count}")
        summary_lines.append(f"💵 **Paid Resources**: {paid_count}")
        
        summary_output = "\n".join(summary_lines)
        
        return f"{summary_output}\n\n{table_output}"
    
    @staticmethod
    def format_diff_summary(resource_diffs: List[ResourceDiff]) -> str:
        """Format a summary of resource changes into a readable table."""
        if not resource_diffs:
            return "📋 No changes to display."
        
        table_data = []
        
        for diff in resource_diffs:
            # Add emoji based on change type
            if diff.change_type == "ADD":
                emoji = "➕"
            elif diff.change_type == "REMOVE":
                emoji = "❌"
            elif diff.change_type == "MODIFY":
                emoji = "🔄"
            else:
                emoji = "❓"
            
            # Shorten resource type for better display
            resource_type = diff.resource_type.replace("AWS::", "").replace("::", ":")
            
            # Format property changes
            property_changes = []
            for prop, (old_val, new_val) in diff.property_changes.items():
                if old_val is None:
                    property_changes.append(f"+ {prop}: {new_val}")
                elif new_val is None:
                    property_changes.append(f"- {prop}: {old_val}")
                else:
                    property_changes.append(f"~ {prop}: {old_val} → {new_val}")
            
            table_data.append([
                f"{emoji} {diff.change_type}",
                resource_type,
                diff.logical_id[:15] + "..." if len(diff.logical_id) > 15 else diff.logical_id,
                "\n".join(property_changes[:3]) if property_changes else "No changes"  # Limit to 3 changes
            ])
        
        headers = ["🔄 Change", "🏗️ Type", "🆔 ID", "📝 Changes"]
        
        return tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")
    
    @staticmethod
    def format_full_report(
        old_costs: List[ResourceCost],
        new_costs: List[ResourceCost],
        resource_diffs: List[ResourceDiff]
    ) -> str:
        """Format a complete cost estimation report."""
        report = []
        
        # Add header with emojis
        report.append("# 💰 CloudFormation Stack Cost Estimation Report\n")
        
        # Add summary section
        report.append("## 📊 Summary\n")
        old_total = sum(rc.monthly_cost for rc in old_costs)
        new_total = sum(rc.monthly_cost for rc in new_costs)
        cost_diff = new_total - old_total
        
        # Add emojis for cost impact
        if cost_diff > 0:
            impact_emoji = "📈"
            impact_text = "Increase"
        elif cost_diff < 0:
            impact_emoji = "📉"
            impact_text = "Decrease"
        else:
            impact_emoji = "➡️"
            impact_text = "No Change"
        
        report.append(f"💵 Current Monthly Cost: ${old_total:.2f}")
        report.append(f"💰 New Monthly Cost: ${new_total:.2f}")
        report.append(f"📊 Monthly Cost Difference: ${cost_diff:.2f}")
        report.append(f"{impact_emoji} Cost Impact: {impact_text}\n")
        
        # Add changes section
        if resource_diffs:
            report.append("## 🔄 Resource Changes\n")
            report.append(CostReportFormatter.format_diff_summary(resource_diffs))
            report.append("\n")
        
        # Add detailed cost breakdown
        report.append("## 📋 Detailed Cost Breakdown\n")
        
        if old_costs:
            report.append("### 📦 Current Resources\n")
            report.append(CostReportFormatter.format_cost_summary(old_costs))
            report.append("\n")
        
        if new_costs:
            report.append("### 🆕 New Resources\n")
            report.append(CostReportFormatter.format_cost_summary(new_costs))
            report.append("\n")
        
        # Add notes section
        report.append("## 📝 Notes\n")
        report.append("💡 All costs are estimates based on current AWS pricing")
        report.append("⚠️ Usage-based costs are not included in the estimates")
        report.append("📈 Costs may vary based on actual usage patterns")
        report.append("🔍 Some resources may have additional costs not shown here")
        
        return "\n".join(report)
    
    @staticmethod
    def format_github_comment(
        old_costs: List[ResourceCost],
        new_costs: List[ResourceCost],
        resource_diffs: List[ResourceDiff]
    ) -> str:
        """Format a GitHub comment with cost estimation results."""
        report = []
        
        # Add summary with emojis
        old_total = sum(rc.monthly_cost for rc in old_costs)
        new_total = sum(rc.monthly_cost for rc in new_costs)
        cost_diff = new_total - old_total
        
        # Calculate percentage change
        if old_total == 0:
            percent_change = "N/A"
        else:
            percent_change = f"{('+' if cost_diff > 0 else '')}{cost_diff/old_total*100:.1f}%"
        
        # Add impact emoji
        if cost_diff > 0:
            impact_emoji = "📈"
        elif cost_diff < 0:
            impact_emoji = "📉"
        else:
            impact_emoji = "➡️"
        
        report.append("## 💰 Cost Estimation Results\n")
        report.append(f"{impact_emoji} Monthly cost impact: **${cost_diff:.2f}** ({percent_change} change)")
        report.append(f"- Current: ${old_total:.2f}/month")
        report.append(f"- New: ${new_total:.2f}/month\n")
        
        # Add resource changes
        if resource_diffs:
            report.append("### 🔄 Resource Changes\n")
            report.append(CostReportFormatter.format_diff_summary(resource_diffs))
            report.append("\n")
        
        # Add cost breakdown
        report.append("### 📋 Cost Breakdown\n")
        report.append(CostReportFormatter.format_cost_summary(new_costs))
        
        return "\n".join(report)
    
    @staticmethod
    def format_single_template_breakdown(resource_costs: List[ResourceCost]) -> str:
        """Format cost breakdown for a single template (new deployment scenario)."""
        if not resource_costs:
            return "📋 No resources found in template."
        
        # Calculate totals
        total_hourly = sum(rc.hourly_cost for rc in resource_costs if rc.pricing_model != "usage_based")
        total_monthly = sum(rc.monthly_cost for rc in resource_costs if rc.pricing_model != "usage_based")
        usage_based_count = len([rc for rc in resource_costs if rc.pricing_model == "usage_based"])
        free_count = len([rc for rc in resource_costs if rc.pricing_model == "free"])
        paid_count = len([rc for rc in resource_costs if rc.pricing_model not in ["free", "usage_based"]])
        
        # Create header
        report = []
        report.append("# 💰 CloudFormation Stack Cost Breakdown")
        report.append("=" * 60)
        report.append("")
        
        # Summary section
        report.append("## 📊 Cost Summary")
        report.append(f"💰 **Fixed Monthly Cost**: ${total_monthly:.2f}")
        report.append(f"⏰ **Fixed Hourly Cost**: ${total_hourly:.4f}")
        report.append(f"📊 **Usage-Based Resources**: {usage_based_count} (costs depend on usage)")
        report.append(f"🆓 **Free Resources**: {free_count}")
        report.append(f"💵 **Paid Resources**: {paid_count}")
        report.append("")
        
        # Detailed breakdown table
        report.append("## 📋 Detailed Resource Breakdown")
        table_data = []
        
        # Sort resources: paid first, then usage-based, then free
        sorted_costs = sorted(resource_costs, key=lambda x: (
            0 if x.pricing_model not in ["free", "usage_based"] and x.monthly_cost > 0 else
            1 if x.pricing_model == "usage_based" else
            2 if x.pricing_model == "free" else
            3
        ))
        
        for rc in sorted_costs:
            # Format resource type
            resource_type = rc.resource_type.replace("AWS::", "")
            
            # Handle tiered pricing resources with sub-breakdown
            if rc.usage_type == "tiered_pricing" and rc.metadata and rc.metadata.get("tier_breakdown"):
                tier_breakdown = rc.metadata["tier_breakdown"]
                
                # Main resource row
                table_data.append([
                    f"📊 {resource_type}",
                    rc.resource_id[:20] + "..." if len(rc.resource_id) > 20 else rc.resource_id,
                    "Usage-based",
                    "Monthly cost depends on usage"
                ])
                
                # Add tier sub-rows (like Infracost does)
                for tier in tier_breakdown["tiers"][:3]:  # Show first 3 tiers
                    table_data.append([
                        f"├─ {tier['description']}",
                        "",
                        tier['price'],
                        "Monthly cost depends on usage"
                    ])
                
                if tier_breakdown["total_tiers"] > 3:
                    table_data.append([
                        f"└─ ... and {tier_breakdown['total_tiers'] - 3} more tiers",
                        "",
                        "Varies",
                        "See detailed breakdown below"
                    ])
                    
            else:
                # Regular resource formatting
                if rc.pricing_model == "free":
                    cost_display = "Free"
                    emoji = "🆓"
                    pricing_info = "This resource is free to use"
                elif rc.pricing_model == "usage_based":
                    cost_display = "Usage-based"
                    emoji = "📊"
                    pricing_info = rc.pricing_details[:60] + "..." if rc.pricing_details and len(rc.pricing_details) > 60 else rc.pricing_details or "Pay per use"
                elif rc.monthly_cost > 0:
                    cost_display = f"${rc.monthly_cost:.2f}/month"
                    emoji = "💰"
                    pricing_info = rc.pricing_details[:60] + "..." if rc.pricing_details and len(rc.pricing_details) > 60 else rc.pricing_details or "Fixed monthly cost"
                else:
                    cost_display = "Unknown"
                    emoji = "❓"
                    pricing_info = "Pricing information not available"
                
                table_data.append([
                    f"{emoji} {resource_type}",
                    rc.resource_id[:20] + "..." if len(rc.resource_id) > 20 else rc.resource_id,
                    cost_display,
                    pricing_info
                ])
        
        headers = ["Resource Type", "Resource ID", "Monthly Cost", "Pricing Details"]
        table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left", maxcolwidths=[None, None, None, 60])
        report.append(table_output)
        
        # Detailed pricing information for tiered resources
        tiered_resources = [rc for rc in resource_costs if rc.usage_type == "tiered_pricing" and rc.metadata and rc.metadata.get("tier_breakdown")]
        if tiered_resources:
            report.append("")
            report.append("## 📊 Detailed Tiered Pricing Information")
            report.append("Complete pricing tiers for usage-based resources:")
            report.append("")
            for rc in tiered_resources:
                resource_type = rc.resource_type.replace("AWS::", "")
                tier_breakdown = rc.metadata["tier_breakdown"]
                
                report.append(f"### {resource_type} ({rc.resource_id})")
                report.append(f"**{tier_breakdown['summary']}**")
                report.append("")
                
                # Show all tiers in a table format
                tier_table_data = []
                for tier in tier_breakdown["tiers"]:
                    tier_table_data.append([
                        f"Tier {tier['tier']}",
                        tier['description'],
                        tier['price']
                    ])
                
                tier_headers = ["Tier", "Usage Range", "Price"]
                tier_table = tabulate(tier_table_data, headers=tier_headers, tablefmt="grid", stralign="left")
                report.append(tier_table)
                report.append("")
        
        # Add footer notes
        report.append("## 📝 Notes")
        report.append("• Fixed costs are predictable monthly charges")
        report.append("• Usage-based costs depend on actual resource utilization")
        report.append("• Tiered pricing means cost per unit decreases with higher usage")
        report.append("• Free resources have no direct charges but may incur costs through usage")
        report.append("• Estimates are based on current AWS pricing and may vary")
        
        return "\n".join(report)
    
    @staticmethod
    def format_cost_comparison_table(
        old_costs: List[ResourceCost],
        new_costs: List[ResourceCost],
        resource_diffs: List[ResourceDiff]
    ) -> str:
        """Format a cost comparison table between old and new templates."""
        # Calculate totals (exclude usage-based from fixed cost totals)
        old_total = sum(rc.monthly_cost for rc in old_costs if rc.pricing_model != "usage_based")
        new_total = sum(rc.monthly_cost for rc in new_costs if rc.pricing_model != "usage_based")
        cost_diff = new_total - old_total
        
        # Count resources by type for both old and new
        old_usage_based = len([rc for rc in old_costs if rc.pricing_model == "usage_based"])
        new_usage_based = len([rc for rc in new_costs if rc.pricing_model == "usage_based"])
        old_free = len([rc for rc in old_costs if rc.pricing_model == "free"])
        new_free = len([rc for rc in new_costs if rc.pricing_model == "free"])
        old_paid = len([rc for rc in old_costs if rc.pricing_model not in ["free", "usage_based"] and rc.monthly_cost > 0])
        new_paid = len([rc for rc in new_costs if rc.pricing_model not in ["free", "usage_based"] and rc.monthly_cost > 0])
        
        # Create header
        report = []
        report.append("# 💰 CloudFormation Stack Cost Comparison")
        report.append("=" * 60)
        report.append("")
        
        # Summary section
        report.append("## 📊 Cost Impact Summary")
        if cost_diff > 0:
            impact_emoji = "📈"
            impact_text = "INCREASE"
        elif cost_diff < 0:
            impact_emoji = "📉"
            impact_text = "DECREASE"
        else:
            impact_emoji = "➡️"
            impact_text = "NO CHANGE"
        
        percent_change = "N/A" if old_total == 0 else f"{(cost_diff/old_total*100):+.1f}%"
        
        report.append(f"💵 **Current Monthly Cost**: ${old_total:.2f}")
        report.append(f"💰 **New Monthly Cost**: ${new_total:.2f}")
        report.append(f"{impact_emoji} **Monthly Cost {impact_text}**: ${cost_diff:+.2f} ({percent_change})")
        report.append("")
        
        # Resource changes summary
        if resource_diffs:
            added = len([d for d in resource_diffs if d.change_type == "ADD"])
            removed = len([d for d in resource_diffs if d.change_type == "REMOVE"])
            modified = len([d for d in resource_diffs if d.change_type == "MODIFY"])
            
            report.append("## 🔄 Resource Changes Summary")
            report.append(f"➕ **Added**: {added} resources")
            report.append(f"❌ **Removed**: {removed} resources")
            report.append(f"🔄 **Modified**: {modified} resources")
            report.append("")
        
        # Resource type comparison
        report.append("## 📊 Resource Type Comparison")
        comparison_table = [
            ["💰 Fixed Cost Resources", f"{old_paid}", f"{new_paid}", f"{new_paid - old_paid:+d}"],
            ["📊 Usage-Based Resources", f"{old_usage_based}", f"{new_usage_based}", f"{new_usage_based - old_usage_based:+d}"],
            ["🆓 Free Resources", f"{old_free}", f"{new_free}", f"{new_free - old_free:+d}"]
        ]
        comparison_headers = ["Resource Type", "Current", "New", "Change"]
        comparison_output = tabulate(comparison_table, headers=comparison_headers, tablefmt="grid", stralign="center")
        report.append(comparison_output)
        report.append("")
        
        # Detailed cost breakdown with Infracost-style formatting
        report.append("## 📋 New Template Cost Breakdown")
        if new_costs:
            # Create cost breakdown table with tiered pricing support
            table_data = []
            sorted_costs = sorted(new_costs, key=lambda x: (
                0 if x.pricing_model not in ["free", "usage_based"] and x.monthly_cost > 0 else
                1 if x.pricing_model == "usage_based" else
                2 if x.pricing_model == "free" else
                3
            ))
            
            for rc in sorted_costs:
                resource_type = rc.resource_type.replace("AWS::", "")
                
                # Handle tiered pricing resources with sub-breakdown
                if rc.usage_type == "tiered_pricing" and rc.metadata and rc.metadata.get("tier_breakdown"):
                    tier_breakdown = rc.metadata["tier_breakdown"]
                    
                    # Main resource row
                    table_data.append([
                        f"📊 {resource_type}",
                        rc.resource_id[:18] + "..." if len(rc.resource_id) > 18 else rc.resource_id,
                        "Usage-based",
                        "Monthly cost depends on usage"
                    ])
                    
                    # Add tier sub-rows (like Infracost does)
                    for tier in tier_breakdown["tiers"][:3]:  # Show first 3 tiers
                        table_data.append([
                            f"├─ {tier['description']}",
                            "",
                            tier['price'],
                            "Monthly cost depends on usage"
                        ])
                    
                    if tier_breakdown["total_tiers"] > 3:
                        table_data.append([
                            f"└─ ... and {tier_breakdown['total_tiers'] - 3} more tiers",
                            "",
                            "Varies",
                            "See detailed breakdown below"
                        ])
                        
                else:
                    # Regular resource formatting
                    if rc.pricing_model == "free":
                        cost_display = "Free"
                        emoji = "🆓"
                        pricing_info = "This resource is free to use"
                    elif rc.pricing_model == "usage_based":
                        cost_display = "Usage-based"
                        emoji = "📊"
                        pricing_info = rc.pricing_details[:50] + "..." if rc.pricing_details and len(rc.pricing_details) > 50 else rc.pricing_details or "Pay per use"
                    elif rc.monthly_cost > 0:
                        cost_display = f"${rc.monthly_cost:.2f}/month"
                        emoji = "💰"
                        pricing_info = rc.pricing_details[:50] + "..." if rc.pricing_details and len(rc.pricing_details) > 50 else rc.pricing_details or "Fixed monthly cost"
                    else:
                        cost_display = "Unknown"
                        emoji = "❓"
                        pricing_info = "Pricing information not available"
                    
                    table_data.append([
                        f"{emoji} {resource_type}",
                        rc.resource_id[:18] + "..." if len(rc.resource_id) > 18 else rc.resource_id,
                        cost_display,
                        pricing_info
                    ])
            
            headers = ["Resource Type", "Resource ID", "Monthly Cost", "Pricing Details"]
            table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left", maxcolwidths=[None, None, None, 50])
            report.append(table_output)
        else:
            report.append("No resources found in new template.")
        
        # Detailed pricing information for tiered resources
        tiered_resources = [rc for rc in new_costs if rc.usage_type == "tiered_pricing" and rc.metadata and rc.metadata.get("tier_breakdown")]
        if tiered_resources:
            report.append("")
            report.append("## 📊 Detailed Tiered Pricing Information")
            report.append("Complete pricing tiers for usage-based resources:")
            report.append("")
            for rc in tiered_resources:
                resource_type = rc.resource_type.replace("AWS::", "")
                tier_breakdown = rc.metadata["tier_breakdown"]
                
                report.append(f"### {resource_type} ({rc.resource_id})")
                report.append(f"**{tier_breakdown['summary']}**")
                report.append("")
                
                # Show all tiers in a table format
                tier_table_data = []
                for tier in tier_breakdown["tiers"]:
                    tier_table_data.append([
                        f"Tier {tier['tier']}",
                        tier['description'],
                        tier['price']
                    ])
                
                tier_headers = ["Tier", "Usage Range", "Price"]
                tier_table = tabulate(tier_table_data, headers=tier_headers, tablefmt="grid", stralign="left")
                report.append(tier_table)
                report.append("")
        
        # Add footer notes
        report.append("## 📝 Notes")
        report.append("• Fixed costs are predictable monthly charges")
        report.append("• Usage-based costs depend on actual resource utilization")
        report.append("• Tiered pricing means cost per unit decreases with higher usage")
        report.append("• Free resources have no direct charges but may incur costs through usage")
        report.append("• Estimates are based on current AWS pricing and may vary")
        
        return "\n".join(report) 