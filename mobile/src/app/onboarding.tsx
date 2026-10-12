import { router } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import {
  BackHandler,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type KeyboardTypeOptions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { PrimaryButton, useAuthTheme } from '@/components/auth';

type Step = {
  key: string;
  title: string;
  subtitle: string;
  optional?: boolean;
} & (
  | {
      kind: 'input';
      placeholder: string;
      unit?: string;
      keyboardType?: KeyboardTypeOptions;
      range?: [number, number];
      maxLength?: number;
    }
  | { kind: 'choice' | 'multi'; options: string[] }
);

const STEPS: Step[] = [
  {
    key: 'name',
    kind: 'input',
    title: "What's your\nname?",
    subtitle: 'So we know what to call you.',
    placeholder: 'Your name',
    maxLength: 60,
  },
  {
    key: 'age',
    kind: 'input',
    title: 'How old\nare you?',
    subtitle: 'Normal lab ranges change with age.',
    placeholder: '25',
    unit: 'years',
    keyboardType: 'number-pad',
    range: [1, 120],
    maxLength: 3,
  },
  {
    key: 'sex',
    kind: 'choice',
    title: "What's your\nsex?",
    subtitle: 'Many reference ranges differ by sex.',
    options: ['Female', 'Male', 'Other'],
  },
  {
    key: 'height',
    kind: 'input',
    title: 'How tall\nare you?',
    subtitle: 'Used to work out your daily calorie needs.',
    placeholder: '170',
    unit: 'cm',
    keyboardType: 'decimal-pad',
    range: [50, 250],
    maxLength: 5,
  },
  {
    key: 'weight',
    kind: 'input',
    title: 'How much do\nyou weigh?',
    subtitle: 'Used to work out your daily calorie needs.',
    placeholder: '65',
    unit: 'kg',
    keyboardType: 'decimal-pad',
    range: [10, 300],
    maxLength: 5,
  },
  {
    key: 'diet',
    kind: 'choice',
    title: 'What do\nyou eat?',
    subtitle: 'Your meal plan will only use foods that fit.',
    options: ['Vegetarian', 'Eggetarian', 'Non-vegetarian', 'Vegan'],
  },
  {
    key: 'conditions',
    kind: 'multi',
    optional: true,
    title: 'Any health\nconditions?',
    subtitle: 'Select all that apply.',
    options: ['Diabetes', 'Thyroid', 'Blood pressure', 'Cholesterol', 'PCOS', 'Kidney', 'None'],
  },
  {
    key: 'allergies',
    kind: 'input',
    optional: true,
    title: 'Any food\nallergies?',
    subtitle: "We'll keep these out of your meal plan.",
    placeholder: 'e.g. peanuts, lactose',
    maxLength: 120,
  },
];

type Answers = Record<string, string | string[]>;

/** Returns an error message, or undefined when the answer is acceptable. */
function validate(step: Step, value: string | string[] | undefined): string | undefined {
  if (step.kind !== 'input') {
    return step.optional || (value?.length ?? 0) > 0 ? undefined : 'Select an option';
  }
  const v = typeof value === 'string' ? value.trim() : '';
  if (!v) return step.optional ? undefined : 'This is required';
  if (step.range) {
    const n = Number(v);
    const [min, max] = step.range;
    if (!(n >= min && n <= max)) return `Enter a number between ${min} and ${max}`;
  }
}

export default function Onboarding() {
  const { c, styles } = useAuthTheme();
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [error, setError] = useState<string>();

  const step = STEPS[index];
  const value = answers[step.key];
  const last = index === STEPS.length - 1;

  const set = (v: string | string[]) => {
    setAnswers((a) => ({ ...a, [step.key]: v }));
    setError(undefined);
  };

  function next() {
    const err = validate(step, value);
    if (err) return setError(err);
    if (!last) return setIndex(index + 1);
    // ponytail: no backend yet, send `answers` to the profile API here
    router.replace('/home');
  }

  function back() {
    setError(undefined);
    setIndex(index - 1);
  }

  // Android back button steps back through questions instead of leaving onboarding
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (index === 0) return false;
      back();
      return true;
    });
    return () => sub.remove();
  });

  function toggle(option: string) {
    if (step.kind === 'choice') return set([option]);
    const selected = (value as string[] | undefined) ?? [];
    // "None" is exclusive: picking it clears the rest, picking anything else clears it
    if (option === 'None') return set(selected.includes('None') ? [] : ['None']);
    const rest = selected.filter((x) => x !== 'None');
    set(rest.includes(option) ? rest.filter((x) => x !== option) : [...rest, option]);
  }

  return (
    <SafeAreaView style={styles.flex}>
      <StatusBar style={c.statusBar} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={local.topBar}>
          <Pressable
            onPress={back}
            disabled={index === 0}
            accessibilityRole="button"
            accessibilityLabel="Previous question"
            style={[local.iconBtn, index === 0 && local.hidden]}>
            <SymbolView
              name={{ ios: 'chevron.left', android: 'arrow_back', web: 'arrow_back' }}
              size={22}
              tintColor={c.title}
            />
          </Pressable>
          <View
            style={[local.track, { backgroundColor: c.border }]}
            accessible
            accessibilityRole="progressbar"
            accessibilityLabel={`Question ${index + 1} of ${STEPS.length}`}>
            <View
              style={[
                local.fill,
                { backgroundColor: c.title, width: `${((index + 1) / STEPS.length) * 100}%` },
              ]}
            />
          </View>
          <Text style={[local.count, { color: c.muted }]}>
            {index + 1}/{STEPS.length}
          </Text>
        </View>

        <ScrollView
          key={step.key}
          contentContainerStyle={local.body}
          keyboardShouldPersistTaps="handled">
          <Text style={styles.title} accessibilityRole="header">
            {step.title}
          </Text>
          <Text style={styles.subtitle}>{step.subtitle}</Text>

          {step.kind === 'input' ? (
            <View style={[local.bigField, { borderBottomColor: error ? c.error : c.title }]}>
              <TextInput
                style={[local.bigInput, { color: c.text }]}
                value={(value as string) ?? ''}
                onChangeText={set}
                placeholder={step.placeholder}
                placeholderTextColor={c.placeholder}
                keyboardType={step.keyboardType}
                maxLength={step.maxLength}
                autoCapitalize={step.key === 'name' ? 'words' : 'sentences'}
                autoComplete={step.key === 'name' ? 'name' : 'off'}
                accessibilityLabel={step.title.replace('\n', ' ')}
                autoFocus
                returnKeyType={last ? 'done' : 'next'}
                onSubmitEditing={next}
              />
              {!!step.unit && <Text style={[local.unit, { color: c.muted }]}>{step.unit}</Text>}
            </View>
          ) : (
            <View
              style={local.options}
              accessibilityRole={step.kind === 'choice' ? 'radiogroup' : undefined}>
              {step.options.map((o) => {
                const on = ((value as string[] | undefined) ?? []).includes(o);
                return (
                  <Pressable
                    key={o}
                    onPress={() => toggle(o)}
                    accessibilityRole={step.kind === 'choice' ? 'radio' : 'checkbox'}
                    accessibilityState={{ checked: on }}
                    style={({ pressed }) => [
                      local.option,
                      { borderColor: on ? c.title : c.border, backgroundColor: c.surface },
                      pressed && styles.pressed,
                    ]}>
                    <Text style={[local.optionText, { color: c.text }]}>{o}</Text>
                    <View
                      style={[
                        step.kind === 'choice' ? local.radio : local.checkbox,
                        { borderColor: on ? c.title : c.border },
                        on && { backgroundColor: c.title },
                      ]}>
                      {on && (
                        <SymbolView
                          name={{ ios: 'checkmark', android: 'check', web: 'check' }}
                          size={14}
                          tintColor={c.bg}
                        />
                      )}
                    </View>
                  </Pressable>
                );
              })}
            </View>
          )}
          {!!error && <Text style={styles.error}>{error}</Text>}
        </ScrollView>

        <View style={local.footer}>
          <PrimaryButton title={last ? 'Finish' : 'Continue'} onPress={next} />
          {step.optional && (
            <Pressable
              onPress={() => {
                setAnswers((a) => ({ ...a, [step.key]: step.kind === 'input' ? '' : [] }));
                setError(undefined);
                if (last) router.replace('/home');
                else setIndex(index + 1);
              }}
              accessibilityRole="button"
              style={styles.linkHit}>
              <Text style={styles.link}>Skip</Text>
            </Pressable>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const local = StyleSheet.create({
  topBar: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 12 },
  iconBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  hidden: { opacity: 0 },
  track: { flex: 1, height: 6, borderRadius: 3, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 3 },
  count: { minWidth: 32, fontSize: 13, fontWeight: '600', textAlign: 'right', marginRight: 12 },
  body: { flexGrow: 1, paddingHorizontal: 24, paddingTop: 32, paddingBottom: 24 },
  bigField: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 40,
    borderBottomWidth: 2,
  },
  bigInput: { flex: 1, fontSize: 32, fontWeight: '600', minHeight: 64 },
  unit: { fontSize: 20, fontWeight: '600' },
  options: { marginTop: 32, gap: 12 },
  option: {
    minHeight: 60,
    paddingHorizontal: 20,
    borderRadius: 16,
    borderWidth: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  optionText: { fontSize: 17, fontWeight: '600' },
  radio: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 7,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  footer: { paddingHorizontal: 24, paddingBottom: 16 },
});
