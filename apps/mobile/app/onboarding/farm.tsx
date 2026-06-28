import { useState } from "react";
import { router } from "expo-router";
import { ProtectedScreen } from "../../components/auth/protected-screen";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "./ui";

function isPositiveNumber(value: string): boolean {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0;
}

export default function FarmScreen() {
  const [name, setName] = useState("");
  const [village, setVillage] = useState("");
  const [totalAcreage, setTotalAcreage] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function continueToPlot() {
    const nextErrors: Record<string, string> = {};
    if (!name.trim()) {
      nextErrors.name = "Farm name is required.";
    }
    if (!village.trim()) {
      nextErrors.village = "Farm village is required.";
    }
    if (!totalAcreage) {
      nextErrors.totalAcreage = "Total acreage is required.";
    } else if (!isPositiveNumber(totalAcreage)) {
      nextErrors.totalAcreage = "Total acreage must be greater than zero.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length === 0) {
      router.push("/onboarding/plot");
    }
  }

  return (
    <ProtectedScreen requiredPermissions={["farms:write"]}>
      <OnboardingScreen eyebrow="Step 3" title="Farm Profile">
        <Field error={errors.name} label="Farm name" onChangeText={setName} placeholder="North field farm" value={name} />
        <Field error={errors.village} label="Farm village" onChangeText={setVillage} placeholder="Village name" value={village} />
        <Field
          error={errors.totalAcreage}
          keyboardType="decimal-pad"
          label="Total acreage"
          onChangeText={setTotalAcreage}
          placeholder="2.50"
          value={totalAcreage}
        />
        <ButtonRow>
          <ActionButton label="Back" variant="secondary" onPress={() => router.back()} />
          <ActionButton label="Continue" onPress={continueToPlot} />
        </ButtonRow>
      </OnboardingScreen>
    </ProtectedScreen>
  );
}
