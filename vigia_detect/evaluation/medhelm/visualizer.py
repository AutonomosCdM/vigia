"""
MedHELM Evaluation Visualizer
============================

Creates visualizations for MedHELM evaluation results.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime


class MedHELMVisualizer:
    """Create visualizations for MedHELM evaluation results."""
    
    def __init__(self, output_dir: str = "./evaluation_results/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
    
    def create_capability_heatmap(self, heatmap_data: List[Dict[str, Any]], 
                                 save_path: Optional[str] = None):
        """Create capability heatmap showing Vigía's coverage of MedHELM tasks."""
        # Convert to DataFrame
        df = pd.DataFrame(heatmap_data)
        
        # Pivot for heatmap
        pivot_df = df.pivot_table(
            index='subcategory',
            columns='category',
            values='score',
            aggfunc='mean'
        )
        
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Custom colormap: red (0) -> yellow (0.5) -> green (1)
        colors = ['#d32f2f', '#ffc107', '#4caf50']
        cmap = sns.blend_palette(colors, n_colors=100, as_cmap=True)
        
        # Create heatmap
        ax = sns.heatmap(
            pivot_df,
            annot=True,
            fmt='.2f',
            cmap=cmap,
            vmin=0,
            vmax=1,
            cbar_kws={'label': 'Capability Level'},
            linewidths=0.5
        )
        
        # Customize
        plt.title('Vigía MedHELM Capability Coverage Heatmap', fontsize=16, pad=20)
        plt.xlabel('MedHELM Category', fontsize=12)
        plt.ylabel('Subcategory', fontsize=12)
        
        # Rotate labels
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, fc='#4caf50', label='Strong (1.0)'),
            plt.Rectangle((0,0),1,1, fc='#ffc107', label='Partial (0.5)'),
            plt.Rectangle((0,0),1,1, fc='#ff9800', label='Planned (0.25)'),
            plt.Rectangle((0,0),1,1, fc='#d32f2f', label='N/A or None (0)')
        ]
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.15, 1))
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = self.output_dir / f"capability_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def create_performance_comparison(self, evaluation_results: Dict[str, Any],
                                    baseline_scores: Dict[str, float] = None,
                                    save_path: Optional[str] = None):
        """Create performance comparison chart."""
        # Extract metrics by category
        categories = []
        vigia_scores = []
        
        for category, results in evaluation_results.get('results_by_category', {}).items():
            if results:
                # Calculate average accuracy/score for category
                scores = []
                for result in results:
                    if result['success'] and result['metrics']:
                        # Get primary metric (accuracy or f1_score)
                        for metric_name in ['accuracy', 'f1_score', 'clinical_relevance']:
                            if metric_name in result['metrics']:
                                scores.append(result['metrics'][metric_name]['value'])
                                break
                
                if scores:
                    categories.append(category)
                    vigia_scores.append(np.mean(scores))
        
        if not categories:
            print("No performance data to visualize")
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = np.arange(len(categories))
        width = 0.35
        
        # Vigía scores
        bars1 = ax.bar(x - width/2, vigia_scores, width, label='Vigía', color='#2196f3')
        
        # Add baseline if provided
        if baseline_scores:
            baseline_values = [baseline_scores.get(cat, 0.5) for cat in categories]
            bars2 = ax.bar(x + width/2, baseline_values, width, label='Baseline', color='#9e9e9e')
        
        # Customize
        ax.set_xlabel('MedHELM Category', fontsize=12)
        ax.set_ylabel('Performance Score', fontsize=12)
        ax.set_title('Vigía Performance by MedHELM Category', fontsize=16, pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 1.0)
        
        # Add value labels on bars
        for bars in [bars1]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = self.output_dir / f"performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def create_coverage_pie_chart(self, capability_summary: Dict[str, Any],
                                 save_path: Optional[str] = None):
        """Create pie chart showing capability coverage."""
        # Extract data
        by_level = capability_summary.get('by_level', {})
        
        labels = []
        sizes = []
        colors = []
        
        level_colors = {
            'strong': '#4caf50',
            'partial': '#ffc107',
            'planned': '#ff9800',
            'n/a': '#9e9e9e'
        }
        
        for level, count in by_level.items():
            if count > 0:
                labels.append(f"{level.title()} ({count})")
                sizes.append(count)
                colors.append(level_colors.get(level, '#9e9e9e'))
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 12}
        )
        
        # Customize
        ax.set_title('Vigía Capability Distribution Across MedHELM Tasks', 
                    fontsize=16, pad=20)
        
        # Add coverage percentage as subtitle
        coverage = capability_summary.get('coverage_percentage', 0)
        plt.text(0.5, -0.1, f'Overall Coverage: {coverage:.1f}%',
                transform=ax.transAxes, ha='center', fontsize=14,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = self.output_dir / f"coverage_pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def create_executive_dashboard(self, evaluation_results: Dict[str, Any],
                                 capability_summary: Dict[str, Any],
                                 save_path: Optional[str] = None):
        """Create executive dashboard with key metrics."""
        fig = plt.figure(figsize=(16, 10))
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Overall metrics (top left)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_overall_metrics(ax1, evaluation_results, capability_summary)
        
        # 2. Success rate by category (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_success_rates(ax2, evaluation_results)
        
        # 3. Capability breakdown (middle left)
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_capability_breakdown(ax3, capability_summary)
        
        # 4. Response times (middle center)
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_response_times(ax4, evaluation_results)
        
        # 5. Key strengths (middle right)
        ax5 = fig.add_subplot(gs[1, 2])
        self._plot_key_strengths(ax5, capability_summary)
        
        # 6. Recommendations (bottom)
        ax6 = fig.add_subplot(gs[2, :])
        self._plot_recommendations(ax6)
        
        # Main title
        fig.suptitle('Vigía MedHELM Evaluation Executive Dashboard', 
                    fontsize=20, y=0.98)
        
        # Save
        if save_path is None:
            save_path = self.output_dir / f"executive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def _plot_overall_metrics(self, ax, evaluation_results, capability_summary):
        """Plot overall metrics summary."""
        ax.axis('off')
        
        # Extract metrics
        summary = evaluation_results.get('summary', {})
        coverage = capability_summary.get('coverage_percentage', 0)
        
        metrics_text = f"""
        **OVERALL PERFORMANCE**
        
        Total Tasks Evaluated: {summary.get('total_tasks_evaluated', 0)}
        Successful Tasks: {summary.get('successful_tasks', 0)}
        Success Rate: {summary.get('successful_tasks', 0) / max(1, summary.get('total_tasks_evaluated', 1)) * 100:.1f}%
        
        MedHELM Coverage: {coverage:.1f}%
        Average Runtime: {summary.get('average_runtime', 0):.2f}s
        
        **VIGÍA STRENGTHS**
        • Clinical Decision Support
        • Patient Communication
        • Triage & Workflow
        """
        
        ax.text(0.1, 0.9, metrics_text, transform=ax.transAxes,
               fontsize=12, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    def _plot_success_rates(self, ax, evaluation_results):
        """Plot success rates by category."""
        categories = []
        success_rates = []
        
        for cat, perf in evaluation_results.get('summary', {}).get('category_performance', {}).items():
            categories.append(cat.split()[-1])  # Shorten names
            success_rates.append(perf.get('success_rate', 0) * 100)
        
        if categories:
            bars = ax.bar(categories, success_rates, color='skyblue')
            ax.set_ylabel('Success Rate (%)')
            ax.set_title('Success by Category')
            ax.set_ylim(0, 100)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}%', ha='center', va='bottom')
    
    def _plot_capability_breakdown(self, ax, capability_summary):
        """Plot capability level breakdown."""
        by_level = capability_summary.get('by_level', {})
        
        levels = list(by_level.keys())
        counts = list(by_level.values())
        colors = ['green', 'yellow', 'orange', 'gray']
        
        ax.bar(levels, counts, color=colors)
        ax.set_ylabel('Number of Tasks')
        ax.set_title('Capability Levels')
    
    def _plot_response_times(self, ax, evaluation_results):
        """Plot average response times."""
        categories = []
        avg_times = []
        
        for cat, perf in evaluation_results.get('summary', {}).get('category_performance', {}).items():
            categories.append(cat.split()[-1])  # Shorten names
            avg_times.append(perf.get('average_runtime', 0))
        
        if categories:
            ax.bar(categories, avg_times, color='coral')
            ax.set_ylabel('Avg Runtime (s)')
            ax.set_title('Response Times')
            ax.axhline(y=3, color='r', linestyle='--', label='Target: 3s')
            ax.legend()
    
    def _plot_key_strengths(self, ax, capability_summary):
        """Plot key strengths."""
        ax.axis('off')
        
        strengths_text = """
        **KEY DIFFERENTIATORS**
        
        ✓ NPUAP/EPUAP Compliance
        ✓ Regional Adaptation (MINSAL)
        ✓ Multi-modal Processing
        ✓ 3-Layer Security
        ✓ Real-time Triage
        ✓ WhatsApp Integration
        """
        
        ax.text(0.1, 0.9, strengths_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    def _plot_recommendations(self, ax):
        """Plot recommendations."""
        ax.axis('off')
        
        recommendations_text = """
        **RECOMMENDATIONS FOR IMPROVEMENT**
        
        1. **Expand Clinical Note Generation** - Implement structured templates for automated clinical documentation
        2. **Enhance Research Capabilities** - Add literature review and protocol development features
        3. **Complete Real Dataset Integration** - Activate all 5 medical datasets for production use
        4. **Benchmark Against GPT-4o** - Direct comparison with leading medical LLMs
        5. **Obtain Medical Certification** - Pursue formal medical device certification for clinical deployment
        """
        
        ax.text(0.05, 0.9, recommendations_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))