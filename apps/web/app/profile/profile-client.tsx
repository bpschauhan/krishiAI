"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { SignOutButton, UserButton, useAuth } from "@clerk/nextjs";
import { getDisplayName } from "@krishiai/auth";
import { Button, Card, Input, Label } from "@krishiai/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { getMe, updateMe, type ProfileUpdatePayload } from "../../lib/auth-api";

const phonePattern = /^(?:\+91)?[6-9]\d{9}$/;

const profileSchema = z.object({
  first_name: z.string().max(120).optional(),
  last_name: z.string().max(120).optional(),
  display_name: z.string().max(160).optional(),
  phone_number: z
    .string()
    .optional()
    .refine((value) => !value || phonePattern.test(value.replace(/[\s-]/g, "")), {
      message: "Enter a valid Indian mobile number."
    }),
  preferred_language: z.string().max(32).optional(),
  district: z.string().max(120).optional(),
  village: z.string().max(160).optional()
});

type ProfileForm = z.infer<typeof profileSchema>;

export function ProfileClient() {
  const { getToken, isLoaded } = useAuth();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["me"],
    enabled: isLoaded,
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Missing Clerk session token");
      }
      return getMe(token);
    }
  });

  const form = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      display_name: "",
      phone_number: "",
      preferred_language: "",
      district: "",
      village: ""
    }
  });

  useEffect(() => {
    if (!query.data) {
      return;
    }
    form.reset({
      first_name: query.data.first_name ?? "",
      last_name: query.data.last_name ?? "",
      display_name: query.data.profile?.display_name ?? "",
      phone_number: query.data.profile?.phone_number ?? "",
      preferred_language: query.data.profile?.preferred_language ?? "",
      district: query.data.profile?.district ?? "",
      village: query.data.profile?.village ?? ""
    });
  }, [form, query.data]);

  const mutation = useMutation({
    mutationFn: async (values: ProfileForm) => {
      const token = await getToken();
      if (!token) {
        throw new Error("Missing Clerk session token");
      }
      return updateMe(token, toProfileUpdatePayload(values));
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data);
    }
  });

  return (
    <main className="min-h-screen bg-background px-5 py-8">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Identity</p>
            <h1 className="text-3xl font-semibold text-foreground">Profile</h1>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary">
              <Link href="/dashboard">Dashboard</Link>
            </Button>
            <SignOutButton>
              <Button variant="secondary">Logout</Button>
            </SignOutButton>
            <UserButton />
          </div>
        </header>

        {query.isLoading ? (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">Loading profile...</p>
          </Card>
        ) : null}

        {query.data ? (
          <Card className="p-6">
            <div className="mb-6 space-y-1">
              <h2 className="text-xl font-semibold text-foreground">{getDisplayName(query.data)}</h2>
              <p className="text-sm text-muted-foreground">{query.data.email}</p>
            </div>
            <form className="grid gap-5 sm:grid-cols-2" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <ProfileField error={form.formState.errors.first_name?.message} label="First name">
                <Input {...form.register("first_name")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.last_name?.message} label="Last name">
                <Input {...form.register("last_name")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.display_name?.message} label="Display name">
                <Input {...form.register("display_name")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.phone_number?.message} label="Phone number">
                <Input type="tel" {...form.register("phone_number")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.preferred_language?.message} label="Preferred language">
                <Input {...form.register("preferred_language")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.district?.message} label="District">
                <Input {...form.register("district")} />
              </ProfileField>
              <ProfileField error={form.formState.errors.village?.message} label="Village">
                <Input {...form.register("village")} />
              </ProfileField>
              <div className="flex items-end">
                <Button disabled={mutation.isPending} type="submit">
                  {mutation.isPending ? "Saving..." : "Save profile"}
                </Button>
              </div>
            </form>
            {mutation.isError ? <p className="mt-4 text-sm text-red-600">{mutation.error.message}</p> : null}
            {mutation.isSuccess ? <p className="mt-4 text-sm text-muted-foreground">Profile saved.</p> : null}
          </Card>
        ) : null}
      </section>
    </main>
  );
}

function toProfileUpdatePayload(values: ProfileForm): ProfileUpdatePayload {
  return {
    first_name: values.first_name ?? null,
    last_name: values.last_name ?? null,
    display_name: values.display_name ?? null,
    phone_number: values.phone_number ?? null,
    preferred_language: values.preferred_language ?? null,
    district: values.district ?? null,
    village: values.village ?? null
  };
}

function ProfileField({
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
