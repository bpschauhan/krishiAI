import { useClerk } from "@clerk/clerk-expo";
import { getDisplayName } from "@krishiai/auth";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Text } from "react-native";
import { ProtectedScreen } from "../../components/auth/protected-screen";
import { useMobileAuth } from "../../components/auth/mobile-auth-provider";
import {
  normalizeOptionalText,
  validateIndianPhone
} from "../../lib/mobile-auth-validation";
import { ActionButton, ButtonRow, Field, OnboardingScreen } from "../onboarding/ui";

export default function ProfileScreen() {
  const { signOut } = useClerk();
  const { clearProfile, profile, updateProfile } = useMobileAuth();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [preferredLanguage, setPreferredLanguage] = useState("");
  const [district, setDistrict] = useState("");
  const [village, setVillage] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState("");

  useEffect(() => {
    if (!profile) {
      return;
    }
    setFirstName(profile.first_name ?? "");
    setLastName(profile.last_name ?? "");
    setDisplayName(profile.profile?.display_name ?? "");
    setPhoneNumber(profile.profile?.phone_number ?? "");
    setPreferredLanguage(profile.profile?.preferred_language ?? "");
    setDistrict(profile.profile?.district ?? "");
    setVillage(profile.profile?.village ?? "");
  }, [profile]);

  async function saveProfile() {
    const phoneError = validateIndianPhone(phoneNumber);
    if (phoneError) {
      setErrors({ phoneNumber: phoneError });
      return;
    }

    setIsSaving(true);
    setErrors({});
    setSavedMessage("");
    try {
      await updateProfile({
        first_name: normalizeOptionalText(firstName),
        last_name: normalizeOptionalText(lastName),
        display_name: normalizeOptionalText(displayName),
        phone_number: normalizeOptionalText(phoneNumber),
        preferred_language: normalizeOptionalText(preferredLanguage),
        district: normalizeOptionalText(district),
        village: normalizeOptionalText(village)
      });
      setSavedMessage("Profile saved.");
    } catch (error: unknown) {
      setErrors({ form: error instanceof Error ? error.message : "Unable to save profile." });
    } finally {
      setIsSaving(false);
    }
  }

  async function logout() {
    await signOut();
    clearProfile();
    router.replace("/login");
  }

  return (
    <ProtectedScreen requiredPermissions={["profile:read"]}>
      <OnboardingScreen eyebrow="Profile" title={getDisplayName(profile)}>
        <Field label="First name" onChangeText={setFirstName} placeholder="Ramesh" value={firstName} />
        <Field label="Last name" onChangeText={setLastName} placeholder="Kumar" value={lastName} />
        <Field label="Display name" onChangeText={setDisplayName} placeholder="Ramesh Kumar" value={displayName} />
        <Field
          error={errors.phoneNumber}
          keyboardType="phone-pad"
          label="Phone number"
          onChangeText={setPhoneNumber}
          placeholder="9876543210"
          value={phoneNumber}
        />
        <Field
          label="Preferred language"
          onChangeText={setPreferredLanguage}
          placeholder="Hindi"
          value={preferredLanguage}
        />
        <Field label="District" onChangeText={setDistrict} placeholder="Lucknow" value={district} />
        <Field label="Village" onChangeText={setVillage} placeholder="Village name" value={village} />
        {errors.form ? <Text style={{ color: "#dc2626", fontSize: 13 }}>{errors.form}</Text> : null}
        {savedMessage ? <Text style={{ color: "#15803d", fontSize: 13 }}>{savedMessage}</Text> : null}
        <ButtonRow>
          <ActionButton label="Dashboard" variant="secondary" onPress={() => router.replace("/dashboard")} />
          <ActionButton disabled={isSaving} label={isSaving ? "Saving..." : "Save"} onPress={() => void saveProfile()} />
        </ButtonRow>
        <ActionButton label="Logout" variant="secondary" onPress={() => void logout()} />
      </OnboardingScreen>
    </ProtectedScreen>
  );
}
