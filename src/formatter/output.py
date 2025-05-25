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
            # Add emoji based on cost
            if rc.hourly_cost == 0.0:
                emoji = "🆓" if rc.usage_type == "free" else "💤"
            elif rc.hourly_cost < 0.01:
                emoji = "💰"
            elif rc.hourly_cost < 0.1:
                emoji = "💵"
            else:
                emoji = "💸"
            
            # Shorten resource type for better display
            resource_type = rc.resource_type.replace("AWS::", "").replace("::", ":")
            
            table_data.append([
                f"{emoji} {resource_type}",
                rc.resource_id[:15] + "..." if len(rc.resource_id) > 15 else rc.resource_id,
                f"${rc.hourly_cost:.2f}",
                f"${rc.monthly_cost:.2f}",
                rc.usage_type or "N/A"
            ])
        
        # Add total row
        table_data.append([
            "🔢 TOTAL",
            "",
            f"${total_hourly:.2f}",
            f"${total_monthly:.2f}",
            ""
        ])
        
        headers = ["🏗️ Resource Type", "🆔 ID", "⏰ Hourly", "📅 Monthly", "🏷️ Type"]
        
        return tabulate(table_data, headers=headers, tablefmt="grid", stralign="left")
    
    @staticmethod
    def format_diff_summary(resource_diffs: List[ResourceDiff]) -> str:
        """Format a summary of resource changes into a readable table."""
        if not resource_diffs:
            return "📋 No changes to display."
        
        table_data = []
        
        for diff in resource_diffs:
            # Add emoji based on change type
            if diff.change_type == "CREATE":
                emoji = "➕"
            elif diff.change_type == "DELETE":
                emoji = "❌"
            elif diff.change_type == "UPDATE":
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