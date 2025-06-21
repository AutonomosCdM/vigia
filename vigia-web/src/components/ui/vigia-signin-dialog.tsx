// components/ui/vigia-signin-dialog.tsx
"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as React from "react";
import { cn } from "@/lib/utils";
import { Cross2Icon } from "@radix-ui/react-icons";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Shield, Stethoscope, Hospital, UserCheck } from "lucide-react";
import { useId, useState } from "react";

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogPortal = DialogPrimitive.Portal;
const DialogClose = DialogPrimitive.Close;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-[101] bg-black/80 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-1/2 top-1/2 z-[101] grid max-h-[calc(100%-4rem)] w-full -translate-x-1/2 -translate-y-1/2 gap-4 overflow-y-auto border bg-background p-6 shadow-lg shadow-black/5 duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:max-w-[450px] sm:rounded-xl",
        className,
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="group absolute right-3 top-3 flex size-7 items-center justify-center rounded-lg outline-offset-2 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring/70 disabled:pointer-events-none">
        <Cross2Icon
          width={16}
          height={16}
          strokeWidth={2}
          className="opacity-60 transition-opacity group-hover:opacity-100"
        />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)} {...props} />
);
DialogHeader.displayName = "DialogHeader";

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn("text-lg font-semibold tracking-tight", className)}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

interface VIGIASignInProps {
  onSignIn?: (credentials: { email: string; password: string; department: string; rememberDevice: boolean }) => void;
  hospitalName?: string;
  requireMedicalLicense?: boolean;
}

export function VIGIASignInDialog({ 
  onSignIn, 
  hospitalName = "Hospital Regional de Quilpué",
  requireMedicalLicense = false 
}: VIGIASignInProps) {
  const id = useId();
  const [department, setDepartment] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [medicalLicense, setMedicalLicense] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await onSignIn?.({ 
        email, 
        password, 
        department, 
        rememberDevice 
      });
    } catch (error) {
      console.error("Sign in failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Stethoscope className="w-4 h-4" />
          Access VIGIA System
        </Button>
      </DialogTrigger>
      <DialogContent>
        {/* Medical Header */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-full border-2 border-blue-200 bg-blue-50">
            <Hospital className="w-7 h-7 text-blue-600" />
          </div>
          <DialogHeader>
            <DialogTitle className="sm:text-center">VIGIA Medical Access</DialogTitle>
            <DialogDescription className="sm:text-center">
              {hospitalName}<br />
              Pressure Injury Detection System
            </DialogDescription>
          </DialogHeader>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-4">
            {/* Medical Email */}
            <div className="space-y-2">
              <Label htmlFor={`${id}-email`}>Medical Email</Label>
              <Input 
                id={`${id}-email`} 
                placeholder="doctor@hospital.cl" 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
              />
            </div>

            {/* Password */}
            <div className="space-y-2">
              <Label htmlFor={`${id}-password`}>Password</Label>
              <Input
                id={`${id}-password`}
                placeholder="Enter your secure password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {/* Department Selection */}
            <div className="space-y-2">
              <Label htmlFor={`${id}-department`}>Department</Label>
              <select
                id={`${id}-department`}
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                className="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-sm shadow-black/5 focus-visible:border-ring focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/20"
              >
                <option value="">Select Department</option>
                <option value="emergency">Emergency Medicine</option>
                <option value="internal">Internal Medicine</option>
                <option value="surgery">Surgery</option>
                <option value="icu">Intensive Care Unit</option>
                <option value="geriatrics">Geriatrics</option>
                <option value="nursing">Nursing</option>
                <option value="administration">Administration</option>
              </select>
            </div>

            {/* Medical License (if required) */}
            {requireMedicalLicense && (
              <div className="space-y-2">
                <Label htmlFor={`${id}-license`}>Medical License #</Label>
                <Input
                  id={`${id}-license`}
                  placeholder="MD12345"
                  value={medicalLicense}
                  onChange={(e) => setMedicalLicense(e.target.value)}
                  required={requireMedicalLicense}
                />
              </div>
            )}
          </div>

          {/* Options */}
          <div className="flex justify-between gap-2">
            <div className="flex items-center gap-2">
              <Checkbox 
                id={`${id}-remember`} 
                checked={rememberDevice}
                onCheckedChange={(checked) => setRememberDevice(checked === true)}
              />
              <Label htmlFor={`${id}-remember`} className="font-normal text-muted-foreground">
                Remember this device
              </Label>
            </div>
            <a className="text-sm text-blue-600 underline hover:no-underline" href="#">
              Reset password
            </a>
          </div>

          {/* Sign In Button */}
          <Button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700" 
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Authenticating...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4" />
                Access Medical System
              </div>
            )}
          </Button>
        </form>

        {/* HIPAA Compliance Notice */}
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3">
          <div className="flex items-start gap-2">
            <Shield className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-amber-800">
              <strong>HIPAA Compliance Notice:</strong> This system contains protected health information. 
              Access is restricted to authorized medical personnel only. All activities are logged and monitored.
            </div>
          </div>
        </div>

        {/* Emergency Access */}
        <div className="pt-2 border-t border-gray-200">
          <Button variant="outline" className="w-full text-red-600 border-red-200 hover:bg-red-50">
            Emergency Access Request
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}