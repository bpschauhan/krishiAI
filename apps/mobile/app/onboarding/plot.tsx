import { useState } from "react";
import { router } from "expo-router";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "./ui";

function isPositiveNumber(value: string): boolean {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0;
}

export default function PlotScreen() {
  const [name, setName] = useState("");
  const [acreage, setAcreage] = useState("");
  const [currentCrop, setCurrentCrop] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function finishOnboarding() {
    const nextErrors: Record<string, string> = {};
    if (!name.trim()) {
      nextErrors.name = "Plot name is required.";
    }
    if (!acreage) {
      nextErrors.acreage = "Plot acreage is required.";
    } else if (!isPositiveNumber(acreage)) {
      nextErrors.acreage = "Plot acreage must be greater than zero.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length === 0) {
      router.push("/dashboard");
    }
  }

  return (
    <OnboardingScreen eyebrow="Step 4" title="Plot Profile">
      <Field error={errors.name} label="Plot name" onChangeText={setName} placeholder="Plot A" value={name} />
      <Field
        error={errors.acreage}
        keyboardType="decimal-pad"
        label="Plot acreage"
        onChangeText={setAcreage}
        placeholder="1.25"
        value={acreage}
      />
      <Field label="Current crop" onChangeText={setCurrentCrop} placeholder="Wheat" value={currentCrop} />
      <ButtonRow>
        <ActionButton label="Back" variant="secondary" onPress={() => router.back()} />
        <ActionButton label="Finish" onPress={finishOnboarding} />
      </ButtonRow>
    </OnboardingScreen>
  );
}
