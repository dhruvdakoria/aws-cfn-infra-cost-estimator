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
        total_hourly = sum(rc.hourly_cost for rc in resource_costs)
        total_monthly = sum(rc.monthly_cost for rc in resource_costs)
        currency = resource_costs[0].currency if resource_costs else "USD"
        
        # Create table data
        table_data = []
        for rc in resource_costs:
            # Add emoji based on pricing model and cost
            if rc.pricing_model == "free":
                emoji = "🆓"
                cost_display = "$0.00"
                pricing_info = "Free"
                hourly_display = "$0.00"
            elif rc.pricing_model == "usage_based":
                if rc.monthly_cost > 0:
                    emoji = "💰"
                    cost_display = f"${rc.monthly_cost:.2f}"
                    pricing_info = "Usage-based"
                    hourly_display = f"${rc.hourly_cost:.2f}" if rc.hourly_cost > 0 else "Usage-based"
                else:
                    emoji = "📊"
                    cost_display = "Usage-based"
                    pricing_info = "Pay per use"
                    hourly_display = "Usage-based"
            elif rc.hourly_cost == 0.0:
                emoji = "💤"
                cost_display = "$0.00"
                pricing_info = "Unknown"
                hourly_display = "$0.00"
            elif rc.hourly_cost < 0.01:
                emoji = "💰"
                cost_display = f"${rc.monthly_cost:.2f}"
                pricing_info = "Low cost"
                hourly_display = f"${rc.hourly_cost:.2f}"
            elif rc.hourly_cost < 0.1:
                emoji = "💵"
                cost_display = f"${rc.monthly_cost:.2f}"
                pricing_info = "Moderate cost"
                hourly_display = f"${rc.hourly_cost:.2f}"
            else:
                emoji = "💸"
                cost_display = f"${rc.monthly_cost:.2f}"
                pricing_info = "High cost"
                hourly_display = f"${rc.hourly_cost:.2f}"
            
            # Shorten resource type for better display
            resource_type = rc.resource_type.replace("AWS::", "").replace("::", ":")
            
            # Use pricing details if available for usage-based resources
            if rc.pricing_model == "usage_based" and rc.pricing_details:
                pricing_info = rc.pricing_details[:50] + "..." if len(rc.pricing_details) > 50 else rc.pricing_details
            
            table_data.append([
                f"{emoji} {resource_type}",
                rc.resource_id[:15] + "..." if len(rc.resource_id) > 15 else rc.resource_id,
                hourly_display,
                cost_display,
                pricing_info
            ])
        
        # Add total row
        table_data.append([
            "🔢 TOTAL",
            "",
            f"${total_hourly:.2f}",
            f"${total_monthly:.2f}",
            ""
        ])
        
        headers = ["🏗️ Resource Type", "🆔 ID", "⏰ Hourly", "📅 Monthly", "💡 Pricing Info"]
        
        table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")
        
        # Add detailed pricing information for usage-based resources
        usage_based_resources = [rc for rc in resource_costs if rc.pricing_model == "usage_based"]
        if usage_based_resources:
            table_output += "\n\n📊 **Usage-Based Pricing Details:**\n"
            table_output += "=" * 80 + "\n"
            for rc in usage_based_resources:
                if rc.pricing_details:
                    resource_type = rc.resource_type.replace("AWS::", "")
                    table_output += f"• **{resource_type}** ({rc.resource_id}): {rc.pricing_details}\n"
        
        return table_output
    
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
            
            # Format cost display
            if rc.pricing_model == "free":
                cost_display = "Free"
                emoji = "🆓"
            elif rc.pricing_model == "usage_based":
                cost_display = "Usage-based"
                emoji = "📊"
            elif rc.monthly_cost > 0:
                cost_display = f"${rc.monthly_cost:.2f}/month"
                emoji = "💰"
            else:
                cost_display = "Unknown"
                emoji = "❓"
            
            # Format pricing details
            pricing_info = rc.pricing_details if rc.pricing_details else "No details available"
            if len(pricing_info) > 60:
                pricing_info = pricing_info[:57] + "..."
            
            table_data.append([
                f"{emoji} {resource_type}",
                rc.resource_id[:20] + "..." if len(rc.resource_id) > 20 else rc.resource_id,
                cost_display,
                pricing_info
            ])
        
        headers = ["Resource Type", "Resource ID", "Monthly Cost", "Pricing Details"]
        table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")
        report.append(table_output)
        
        # Usage-based details section
        usage_based_resources = [rc for rc in resource_costs if rc.pricing_model == "usage_based"]
        if usage_based_resources:
            report.append("")
            report.append("## 📊 Usage-Based Pricing Details")
            report.append("These resources charge based on actual usage:")
            report.append("")
            for rc in usage_based_resources:
                resource_type = rc.resource_type.replace("AWS::", "")
                report.append(f"• **{resource_type}** ({rc.resource_id}): {rc.pricing_details}")
        
        # Add footer notes
        report.append("")
        report.append("## 📝 Notes")
        report.append("• Fixed costs are predictable monthly charges")
        report.append("• Usage-based costs depend on actual resource utilization")
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
        # Calculate totals
        old_total = sum(rc.monthly_cost for rc in old_costs if rc.pricing_model != "usage_based")
        new_total = sum(rc.monthly_cost for rc in new_costs if rc.pricing_model != "usage_based")
        cost_diff = new_total - old_total
        
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
        
        # Detailed cost breakdown
        report.append("## 📋 New Template Cost Breakdown")
        if new_costs:
            # Create cost breakdown table
            table_data = []
            sorted_costs = sorted(new_costs, key=lambda x: (
                0 if x.pricing_model not in ["free", "usage_based"] and x.monthly_cost > 0 else
                1 if x.pricing_model == "usage_based" else
                2 if x.pricing_model == "free" else
                3
            ))
            
            for rc in sorted_costs:
                resource_type = rc.resource_type.replace("AWS::", "")
                
                if rc.pricing_model == "free":
                    cost_display = "Free"
                    emoji = "🆓"
                elif rc.pricing_model == "usage_based":
                    cost_display = "Usage-based"
                    emoji = "📊"
                elif rc.monthly_cost > 0:
                    cost_display = f"${rc.monthly_cost:.2f}/month"
                    emoji = "💰"
                else:
                    cost_display = "Unknown"
                    emoji = "❓"
                
                pricing_info = rc.pricing_details if rc.pricing_details else "No details available"
                if len(pricing_info) > 50:
                    pricing_info = pricing_info[:47] + "..."
                
                table_data.append([
                    f"{emoji} {resource_type}",
                    rc.resource_id[:18] + "..." if len(rc.resource_id) > 18 else rc.resource_id,
                    cost_display,
                    pricing_info
                ])
            
            headers = ["Resource Type", "Resource ID", "Monthly Cost", "Pricing Details"]
            table_output = tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")
            report.append(table_output)
        else:
            report.append("No resources found in new template.")
        
        # Usage-based details
        usage_based_resources = [rc for rc in new_costs if rc.pricing_model == "usage_based"]
        if usage_based_resources:
            report.append("")
            report.append("## 📊 Usage-Based Pricing Details")
            report.append("These resources charge based on actual usage:")
            report.append("")
            for rc in usage_based_resources:
                resource_type = rc.resource_type.replace("AWS::", "")
                report.append(f"• **{resource_type}** ({rc.resource_id}): {rc.pricing_details}")
        
        return "\n".join(report) 