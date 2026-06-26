import { useState } from "react";
import { router } from "expo-router";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "./ui";

const phonePattern = /^(?:\+91)?[6-9]\d{9}$/;

export default function FarmerScreen() {
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [village, setVillage] = useState("");
  const [district, setDistrict] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  function continueToFarm() {
    const nextErrors: Record<string, string> = {};
    const normalizedPhone = phoneNumber.replace(/[\s-]/g, "");

    if (!fullName.trim()) {
      nextErrors.fullName = "Farmer name is required.";
    }
    if (!normalizedPhone) {
      nextErrors.phoneNumber = "Phone number is required.";
    } else if (!phonePattern.test(normalizedPhone)) {
      nextErrors.phoneNumber = "Enter a valid Indian mobile number.";
    }
    if (!village.trim()) {
      nextErrors.village = "Village is required.";
    }
    if (!district.trim()) {
      nextErrors.district = "District is required.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length === 0) {
      router.push("/onboarding/farm");
    }
  }

  return (
    <OnboardingScreen eyebrow="Step 2" title="Farmer Profile">
      <Field
        error={errors.fullName}
        label="Full name"
        onChangeText={setFullName}
        placeholder="Ramesh Kumar"
        value={fullName}
      />
      <Field
        error={errors.phoneNumber}
        keyboardType="phone-pad"
        label="Phone number"
        onChangeText={setPhoneNumber}
        placeholder="9876543210"
        value={phoneNumber}
      />
      <Field
        error={errors.village}
        label="Village"
        onChangeText={setVillage}
        placeholder="Village name"
        value={village}
      />
      <Field
        error={errors.district}
        label="District"
        onChangeText={setDistrict}
        placeholder="Lucknow"
        value={district}
      />
      <ButtonRow>
        <ActionButton label="Back" variant="secondary" onPress={() => router.back()} />
        <ActionButton label="Continue" onPress={continueToFarm} />
      </ButtonRow>
    </OnboardingScreen>
  );
}
