"use client";

import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { Button, Card, Input, Label } from "@krishiai/ui";

type District = {
  id: number;
  name: string;
  state: string;
};

type Language = {
  id: number;
  code: string;
  name: string;
};

type Farmer = {
  id: number;
  full_name: string;
  phone_number: string;
  village: string;
  district_id: number;
  language_id: number;
};

type Farm = {
  id: number;
  farmer_id: number;
  district_id: number;
  name: string;
  village: string;
  total_acreage: string;
};

type Plot = {
  id: number;
  farm_id: number;
  name: string;
  acreage: string;
  current_crop: string | null;
};

type FarmerForm = {
  fullName: string;
  phoneNumber: string;
  village: string;
  districtId: string;
};

type FarmForm = {
  name: string;
  village: string;
  totalAcreage: string;
};

type PlotForm = {
  name: string;
  acreage: string;
  currentCrop: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const phonePattern = /^(?:\+91)?[6-9]\d{9}$/;

const fallbackLanguages: Language[] = [
  { id: 1, code: "hi", name: "Hindi" },
  { id: 2, code: "en", name: "English" }
];

const fallbackDistricts: District[] = [
  { id: 1, name: "Lucknow", state: "Uttar Pradesh" },
  { id: 2, name: "Varanasi", state: "Uttar Pradesh" },
  { id: 3, name: "Kanpur Nagar", state: "Uttar Pradesh" }
];

const stepTitles = ["Language", "Farmer Profile", "Farm Profile", "Plot Profile", "Success"];

async function fetchList<T>(path: string, fallback: T[]): Promise<T[]> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as T[];
  } catch {
    return fallback;
  }
}

async function postRecord<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  fallback: TResponse
): Promise<TResponse> {
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      return fallback;
    }
    return (await response.json()) as TResponse;
  } catch {
    return fallback;
  }
}

function isPositiveNumber(value: string): boolean {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0;
}

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [languages, setLanguages] = useState<Language[]>(fallbackLanguages);
  const [districts, setDistricts] = useState<District[]>(fallbackDistricts);
  const [languageId, setLanguageId] = useState("");
  const [farmerForm, setFarmerForm] = useState<FarmerForm>({
    fullName: "",
    phoneNumber: "",
    village: "",
    districtId: ""
  });
  const [farmForm, setFarmForm] = useState<FarmForm>({
    name: "",
    village: "",
    totalAcreage: ""
  });
  const [plotForm, setPlotForm] = useState<PlotForm>({
    name: "",
    acreage: "",
    currentCrop: ""
  });
  const [farmer, setFarmer] = useState<Farmer | null>(null);
  const [farm, setFarm] = useState<Farm | null>(null);
  const [plot, setPlot] = useState<Plot | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    void Promise.all([
      fetchList<Language>("/api/v1/languages", fallbackLanguages),
      fetchList<District>("/api/v1/districts", fallbackDistricts)
    ]).then(([languageData, districtData]) => {
      setLanguages(languageData);
      setDistricts(districtData);
      setLanguageId((current) => current || languageData[0]?.id.toString() || "");
      setFarmerForm((current) => ({
        ...current,
        districtId: current.districtId || districtData[0]?.id.toString() || ""
      }));
    });
  }, []);

  const selectedDistrict = useMemo(
    () => districts.find((district) => district.id.toString() === farmerForm.districtId),
    [districts, farmerForm.districtId]
  );

  function updateFarmerForm(field: keyof FarmerForm) {
    return (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setFarmerForm((current) => ({ ...current, [field]: event.target.value }));
    };
  }

  function updateFarmForm(field: keyof FarmForm) {
    return (event: ChangeEvent<HTMLInputElement>) => {
      setFarmForm((current) => ({ ...current, [field]: event.target.value }));
    };
  }

  function updatePlotForm(field: keyof PlotForm) {
    return (event: ChangeEvent<HTMLInputElement>) => {
      setPlotForm((current) => ({ ...current, [field]: event.target.value }));
    };
  }

  function validateLanguage(): boolean {
    const nextErrors: Record<string, string> = {};
    if (!languageId) {
      nextErrors.languageId = "Language is required.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function validateFarmer(): boolean {
    const nextErrors: Record<string, string> = {};
    if (!farmerForm.fullName.trim()) {
      nextErrors.fullName = "Farmer name is required.";
    }
    const normalizedPhone = farmerForm.phoneNumber.replace(/[\s-]/g, "");
    if (!normalizedPhone) {
      nextErrors.phoneNumber = "Phone number is required.";
    } else if (!phonePattern.test(normalizedPhone)) {
      nextErrors.phoneNumber = "Enter a valid Indian mobile number.";
    }
    if (!farmerForm.village.trim()) {
      nextErrors.village = "Village is required.";
    }
    if (!farmerForm.districtId) {
      nextErrors.districtId = "District is required.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function validateFarm(): boolean {
    const nextErrors: Record<string, string> = {};
    if (!farmForm.name.trim()) {
      nextErrors.farmName = "Farm name is required.";
    }
    if (!farmForm.village.trim()) {
      nextErrors.farmVillage = "Farm village is required.";
    }
    if (!farmForm.totalAcreage) {
      nextErrors.totalAcreage = "Total acreage is required.";
    } else if (!isPositiveNumber(farmForm.totalAcreage)) {
      nextErrors.totalAcreage = "Total acreage must be greater than zero.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function validatePlot(): boolean {
    const nextErrors: Record<string, string> = {};
    if (!plotForm.name.trim()) {
      nextErrors.plotName = "Plot name is required.";
    }
    if (!plotForm.acreage) {
      nextErrors.acreage = "Plot acreage is required.";
    } else if (!isPositiveNumber(plotForm.acreage)) {
      nextErrors.acreage = "Plot acreage must be greater than zero.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  function continueFromLanguage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (validateLanguage()) {
      setStep(1);
    }
  }

  async function submitFarmer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validateFarmer()) {
      return;
    }

    const createdFarmer = await postRecord<Farmer, Record<string, string | number>>(
      "/api/v1/farmers",
      {
        full_name: farmerForm.fullName.trim(),
        phone_number: farmerForm.phoneNumber.trim(),
        village: farmerForm.village.trim(),
        district_id: Number(farmerForm.districtId),
        language_id: Number(languageId)
      },
      {
        id: 1,
        full_name: farmerForm.fullName.trim(),
        phone_number: farmerForm.phoneNumber.trim(),
        village: farmerForm.village.trim(),
        district_id: Number(farmerForm.districtId),
        language_id: Number(languageId)
      }
    );
    setFarmer(createdFarmer);
    setStep(2);
  }

  async function submitFarm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!farmer || !validateFarm()) {
      return;
    }

    const createdFarm = await postRecord<Farm, Record<string, string | number>>(
      "/api/v1/farms",
      {
        farmer_id: farmer.id,
        district_id: Number(farmerForm.districtId),
        name: farmForm.name.trim(),
        village: farmForm.village.trim(),
        total_acreage: farmForm.totalAcreage
      },
      {
        id: 1,
        farmer_id: farmer.id,
        district_id: Number(farmerForm.districtId),
        name: farmForm.name.trim(),
        village: farmForm.village.trim(),
        total_acreage: farmForm.totalAcreage
      }
    );
    setFarm(createdFarm);
    setStep(3);
  }

  async function submitPlot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!farm || !validatePlot()) {
      return;
    }

    const createdPlot = await postRecord<Plot, Record<string, string | number | null>>(
      "/api/v1/plots",
      {
        farm_id: farm.id,
        name: plotForm.name.trim(),
        acreage: plotForm.acreage,
        current_crop: plotForm.currentCrop.trim() || null
      },
      {
        id: 1,
        farm_id: farm.id,
        name: plotForm.name.trim(),
        acreage: plotForm.acreage,
        current_crop: plotForm.currentCrop.trim() || null
      }
    );
    setPlot(createdPlot);
    setStep(4);
  }

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Phase 1 Onboarding</p>
          <h1 className="text-3xl font-semibold text-foreground">KrishiAI farmer setup</h1>
        </div>

        <div className="grid grid-cols-5 gap-2" aria-label="Onboarding progress">
          {stepTitles.map((title, index) => (
            <div
              className={`h-2 rounded-sm ${index <= step ? "bg-primary" : "bg-muted"}`}
              key={title}
              title={title}
            />
          ))}
        </div>

        <Card className="p-6">
          <div className="mb-6 flex flex-col gap-1">
            <p className="text-sm text-muted-foreground">
              Step {step + 1} of {stepTitles.length}
            </p>
            <h2 className="text-xl font-semibold text-foreground">{stepTitles[step]}</h2>
          </div>

          {step === 0 ? (
            <form className="space-y-5" onSubmit={continueFromLanguage}>
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring"
                  id="language"
                  value={languageId}
                  onChange={(event) => setLanguageId(event.target.value)}
                >
                  {languages.map((language) => (
                    <option key={language.id} value={language.id}>
                      {language.name}
                    </option>
                  ))}
                </select>
                {errors.languageId ? <p className="text-sm text-red-600">{errors.languageId}</p> : null}
              </div>
              <Button type="submit">Continue</Button>
            </form>
          ) : null}

          {step === 1 ? (
            <form className="space-y-5" onSubmit={submitFarmer}>
              <FieldError label="Full name" error={errors.fullName}>
                <Input
                  name="fullName"
                  placeholder="Ramesh Kumar"
                  required
                  value={farmerForm.fullName}
                  onChange={updateFarmerForm("fullName")}
                />
              </FieldError>
              <FieldError label="Phone number" error={errors.phoneNumber}>
                <Input
                  name="phoneNumber"
                  placeholder="9876543210"
                  required
                  type="tel"
                  value={farmerForm.phoneNumber}
                  onChange={updateFarmerForm("phoneNumber")}
                />
              </FieldError>
              <FieldError label="Village" error={errors.village}>
                <Input
                  name="village"
                  placeholder="Village name"
                  required
                  value={farmerForm.village}
                  onChange={updateFarmerForm("village")}
                />
              </FieldError>
              <div className="space-y-2">
                <Label htmlFor="district">District</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring"
                  id="district"
                  value={farmerForm.districtId}
                  onChange={updateFarmerForm("districtId")}
                >
                  {districts.map((district) => (
                    <option key={district.id} value={district.id}>
                      {district.name}
                    </option>
                  ))}
                </select>
                {errors.districtId ? <p className="text-sm text-red-600">{errors.districtId}</p> : null}
              </div>
              <div className="flex gap-3">
                <Button type="button" variant="secondary" onClick={() => setStep(0)}>
                  Back
                </Button>
                <Button type="submit">Continue</Button>
              </div>
            </form>
          ) : null}

          {step === 2 ? (
            <form className="space-y-5" onSubmit={submitFarm}>
              <FieldError label="Farm name" error={errors.farmName}>
                <Input
                  name="farmName"
                  placeholder="North field farm"
                  required
                  value={farmForm.name}
                  onChange={updateFarmForm("name")}
                />
              </FieldError>
              <FieldError label="Farm village" error={errors.farmVillage}>
                <Input
                  name="farmVillage"
                  placeholder={farmerForm.village || "Village name"}
                  required
                  value={farmForm.village}
                  onChange={updateFarmForm("village")}
                />
              </FieldError>
              <FieldError label="Total acreage" error={errors.totalAcreage}>
                <Input
                  name="totalAcreage"
                  placeholder="2.50"
                  required
                  type="number"
                  value={farmForm.totalAcreage}
                  onChange={updateFarmForm("totalAcreage")}
                />
              </FieldError>
              <div className="flex gap-3">
                <Button type="button" variant="secondary" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button type="submit">Continue</Button>
              </div>
            </form>
          ) : null}

          {step === 3 ? (
            <form className="space-y-5" onSubmit={submitPlot}>
              <FieldError label="Plot name" error={errors.plotName}>
                <Input
                  name="plotName"
                  placeholder="Plot A"
                  required
                  value={plotForm.name}
                  onChange={updatePlotForm("name")}
                />
              </FieldError>
              <FieldError label="Plot acreage" error={errors.acreage}>
                <Input
                  name="acreage"
                  placeholder="1.25"
                  required
                  type="number"
                  value={plotForm.acreage}
                  onChange={updatePlotForm("acreage")}
                />
              </FieldError>
              <FieldError label="Current crop" error={errors.currentCrop}>
                <Input
                  name="currentCrop"
                  placeholder="Wheat"
                  value={plotForm.currentCrop}
                  onChange={updatePlotForm("currentCrop")}
                />
              </FieldError>
              <div className="flex gap-3">
                <Button type="button" variant="secondary" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button type="submit">Finish</Button>
              </div>
            </form>
          ) : null}

          {step === 4 ? (
            <div className="space-y-5">
              <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
                <SummaryItem label="Farmer" value={farmer?.full_name ?? farmerForm.fullName} />
                <SummaryItem label="District" value={selectedDistrict?.name ?? "Selected district"} />
                <SummaryItem label="Farm" value={farm?.name ?? farmForm.name} />
                <SummaryItem label="Plot" value={plot?.name ?? plotForm.name} />
              </div>
              <Button type="button" onClick={() => window.location.assign("/dashboard")}>
                Open dashboard
              </Button>
            </div>
          ) : null}
        </Card>
      </section>
    </main>
  );
}

function FieldError({
  children,
  error,
  label
}: {
  children: React.ReactNode;
  error: string | undefined;
  label: string;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border p-3">
      <p className="font-medium text-foreground">{label}</p>
      <p>{value}</p>
    </div>
  );
}
