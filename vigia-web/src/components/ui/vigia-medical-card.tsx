// components/ui/vigia-medical-card.tsx
"use client";

import { Heart, Activity, Thermometer, ArrowUpRight, Plus, Target, CheckCircle2, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { cn } from "@/lib/utils";

export interface VitalSignMetric {
  label: string;
  value: string;
  trend: number;
  unit?: "bpm" | "mmHg" | "°C" | "%";
  normalRange?: string;
  status: "normal" | "warning" | "critical";
}

export interface MedicalGoal {
  id: string;
  title: string;
  isCompleted: boolean;
  priority: "low" | "medium" | "high";
}

interface VIGIAMedicalCardProps {
  patientId?: string;
  patientName?: string;
  vitalSigns?: VitalSignMetric[];
  medicalGoals?: MedicalGoal[];
  onAddGoal?: () => void;
  onToggleGoal?: (goalId: string) => void;
  onViewDetails?: () => void;
  className?: string;
}

const VITAL_COLORS = {
  "Heart Rate": "#FF2D55",
  "Blood Pressure": "#007AFF", 
  "Temperature": "#FF9500",
  "O2 Saturation": "#2CD758",
} as const;

const STATUS_COLORS = {
  normal: "#2CD758",
  warning: "#FF9500", 
  critical: "#FF2D55",
} as const;

export function VIGIAMedicalCard({
  patientId = "PAT-001",
  patientName = "María García",
  vitalSigns = [],
  medicalGoals = [],
  onAddGoal,
  onToggleGoal,
  onViewDetails,
  className
}: VIGIAMedicalCardProps) {
  const [isHovering, setIsHovering] = useState<string | null>(null);

  const handleGoalToggle = (goalId: string) => {
    onToggleGoal?.(goalId);
  };

  return (
    <div
      className={cn(
        "relative h-full rounded-3xl p-6",
        "bg-white dark:bg-black/5",
        "border border-zinc-200 dark:border-zinc-800",
        "hover:border-zinc-300 dark:hover:border-zinc-700",
        "transition-all duration-300",
        className
      )}
    >
      {/* Medical Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-full bg-red-50 dark:bg-red-900/20">
          <Heart className="w-5 h-5 text-red-500" />
        </div>
        <div>
          <h3 className="text-lg font-medium text-zinc-900 dark:text-white tracking-tight">
            {patientName}
          </h3>
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            Patient ID: {patientId}
          </p>
        </div>
      </div>

      {/* Vital Signs Rings */}
      <div className="grid grid-cols-2 gap-4">
        {vitalSigns.map((vital, index) => (
          <div
            key={vital.label}
            className="relative flex flex-col items-center"
            onMouseEnter={() => setIsHovering(vital.label)}
            onMouseLeave={() => setIsHovering(null)}
          >
            <div className="relative w-24 h-24">
              {/* Background ring */}
              <div className="absolute inset-0 rounded-full border-4 border-zinc-200 dark:border-zinc-800/50" />
              
              {/* Progress ring */}
              <div
                className={cn(
                  "absolute inset-0 rounded-full border-4 transition-all duration-500",
                  isHovering === vital.label && "scale-105"
                )}
                style={{
                  borderColor: STATUS_COLORS[vital.status],
                  clipPath: `polygon(0 0, 100% 0, 100% ${vital.trend}%, 0 ${vital.trend}%)`,
                }}
              />
              
              {/* Status indicator */}
              {vital.status !== "normal" && (
                <div className="absolute -top-1 -right-1">
                  <AlertTriangle 
                    className={cn(
                      "w-4 h-4",
                      vital.status === "warning" ? "text-orange-500" : "text-red-500"
                    )} 
                  />
                </div>
              )}
              
              {/* Value display */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-lg font-medium text-zinc-900 dark:text-white tracking-tight">
                  {vital.value}
                </span>
                <span className="text-xs text-gray-500 dark:text-zinc-400">
                  {vital.unit}
                </span>
              </div>
            </div>
            
            <span className="mt-3 text-sm font-medium text-zinc-700 dark:text-zinc-300 tracking-tight">
              {vital.label}
            </span>
            <span className="text-xs text-gray-500">
              Normal: {vital.normalRange}
            </span>
          </div>
        ))}
      </div>

      {/* Medical Goals Section */}
      <div className="mt-8 space-y-6">
        <div className="h-px bg-gradient-to-r from-transparent via-zinc-200 dark:via-zinc-800 to-transparent" />

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="flex items-center gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 tracking-tight">
              <Target className="w-4 h-4" />
              Medical Objectives
            </h4>
            <button
              type="button"
              onClick={onAddGoal}
              className="p-1.5 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              <Plus className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
            </button>
          </div>

          <div className="space-y-2">
            {medicalGoals.map((goal) => (
              <button
                key={goal.id}
                onClick={() => handleGoalToggle(goal.id)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-xl",
                  "bg-zinc-50 dark:bg-zinc-900/50",
                  "border border-zinc-200/50 dark:border-zinc-800/50",
                  "hover:border-zinc-300/50 dark:hover:border-zinc-700/50",
                  "transition-all"
                )}
              >
                <CheckCircle2
                  className={cn(
                    "w-5 h-5",
                    goal.isCompleted
                      ? "text-emerald-500"
                      : goal.priority === "high" 
                        ? "text-red-400" 
                        : "text-zinc-400 dark:text-zinc-600"
                  )}
                />
                <span
                  className={cn(
                    "text-sm text-left flex-1 tracking-tight",
                    goal.isCompleted
                      ? "text-gray-500 dark:text-zinc-400 line-through"
                      : "text-zinc-700 dark:text-zinc-300"
                  )}
                >
                  {goal.title}
                </span>
                {goal.priority === "high" && !goal.isCompleted && (
                  <span className="px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full">
                    URGENT
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800">
          <button
            onClick={onViewDetails}
            className="inline-flex items-center gap-2 text-sm font-medium
              text-zinc-600 hover:text-zinc-900 
              dark:text-zinc-400 dark:hover:text-white
              transition-colors duration-200 tracking-tight"
          >
            View Patient Details
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}