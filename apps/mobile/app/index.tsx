import { SafeAreaView, StyleSheet, Text } from "react-native";

export default function IndexScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>KrishiAI Mobile</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f8fafc",
    padding: 24
  },
  title: {
    color: "#0f172a",
    fontSize: 28,
    fontWeight: "700"
  }
});
