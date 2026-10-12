import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';

import {
  AuthScreen,
  Field,
  FooterLink,
  isEmail,
  PrimaryButton,
  SocialButtons,
} from '@/components/auth';

// The param comes from the URL, so tolerate it being missing or malformed
function firstName(profile?: string) {
  try {
    const name = JSON.parse(profile ?? '{}').name;
    return typeof name === 'string' && name.trim() ? name.trim().split(' ')[0] : undefined;
  } catch {
    return undefined;
  }
}

export default function SignUp() {
  // Onboarding answers (name, age, sex, ...) collected before this screen
  const { profile } = useLocalSearchParams<{ profile?: string }>();
  const name = firstName(profile);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  function onSubmit() {
    const next = {
      email: isEmail(email) ? undefined : 'Enter a valid email address',
      password: password.length >= 6 ? undefined : 'Password must be at least 6 characters',
    };
    setErrors(next);
    if (next.email || next.password) return;
    // ponytail: no backend yet, create the account with { email, password, profile } here
    router.push({ pathname: '/verify', params: { email } });
  }

  return (
    <AuthScreen
      title={name ? `Almost done,\n${name}` : 'Create your\naccount'}
      subtitle="Save your profile to get your report insights.">
      <Field
        label="Email"
        placeholder="you@example.com"
        keyboardType="email-address"
        autoComplete="email"
        textContentType="emailAddress"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
      />
      <Field
        label="Password"
        secure
        placeholder="At least 6 characters"
        autoComplete="new-password"
        textContentType="newPassword"
        value={password}
        onChangeText={setPassword}
        onSubmitEditing={onSubmit}
        error={errors.password}
      />
      <PrimaryButton title="Create account" onPress={onSubmit} />
      <SocialButtons />
      <FooterLink
        text="Already have an account?"
        action="Login"
        onPress={() => router.push('/sign-in')}
      />
    </AuthScreen>
  );
}
