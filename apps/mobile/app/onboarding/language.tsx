import { useState } from "react";
import { Pressable, Text, View } from "react-native";
import { router } from "expo-router";
import { ActionButton, OnboardingScreen, styles } from "./ui";

const languages = ["Hindi", "English"];

export default function LanguageScreen() {
  const [language, setLanguage] = useState("Hindi");
  const [error, setError] = useState("");

  function continueToFarmer() {
    if (!language) {
      setError("Language is required.");
      return;
    }
    router.push("/onboarding/farmer");
  }

  return (
    <OnboardingScreen eyebrow="Step 1" title="Language">
      <View style={{ gap: 12 }}>
        {languages.map((option) => (
          <Pressable
            accessibilityRole="button"
            key={option}
            onPress={() => {
              setLanguage(option);
              setError("");
            }}
            style={[
              styles.input,
              {
                justifyContent: "center",
                borderColor: language === option ? "#15803d" : "#cbd5e1"
              }
            ]}
          >
            <Text style={{ color: "#0f172a", fontSize: 16, fontWeight: "700" }}>{option}</Text>
          </Pressable>
        ))}
        {error ? <Text style={styles.error}>{error}</Text> : null}
      </View>
      <ActionButton label="Continue" onPress={continueToFarmer} />
    </OnboardingScreen>
  );
}
