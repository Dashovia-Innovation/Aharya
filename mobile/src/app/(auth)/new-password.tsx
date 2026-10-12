import { router } from 'expo-router';
import { useState } from 'react';

import { AuthScreen, Field, PrimaryButton } from '@/components/auth';

export default function NewPassword() {
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [errors, setErrors] = useState<{ password?: string; confirm?: string }>({});

  function onSubmit() {
    const next = {
      password: password.length >= 6 ? undefined : 'Password must be at least 6 characters',
      confirm: confirm === password ? undefined : 'Passwords do not match',
    };
    setErrors(next);
    if (next.password || next.confirm) return;
    router.dismissTo('/sign-in');
  }

  return (
    <AuthScreen
      title={'Create\nNew Password'}
      subtitle="Your new password must be different from your previous one.">
      <Field
        label="New password"
        secure
        placeholder="At least 6 characters"
        autoComplete="new-password"
        textContentType="newPassword"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
      />
      <Field
        label="Confirm password"
        secure
        placeholder="Re-enter password"
        autoComplete="new-password"
        textContentType="newPassword"
        value={confirm}
        onChangeText={setConfirm}
        onSubmitEditing={onSubmit}
        error={errors.confirm}
      />
      <PrimaryButton title="Save" onPress={onSubmit} />
    </AuthScreen>
  );
}
