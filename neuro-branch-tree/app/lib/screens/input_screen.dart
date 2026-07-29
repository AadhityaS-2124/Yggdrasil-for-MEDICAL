/// Mirrors backend/data/symptom_vocabulary.json for local autocomplete matching.
/// IMPORTANT: Keep this list in sync with the backend's closed vocabulary.
/// This is used ONLY for UI suggestion purposes — the actual parsing/validation
/// still happens server-side via parser_service.py. This file does not enforce
/// anything; it just helps the user know what the system can recognize.
library;

class SymptomEntry {
  final String tag;
  final String plainLabel;
  const SymptomEntry(this.tag, this.plainLabel);
}

const List<SymptomEntry> kSymptomVocabulary = [
  SymptomEntry('resting_tremor', 'Shaking that happens when the limb is at rest'),
  SymptomEntry('action_tremor', 'Shaking that happens during movement'),
  SymptomEntry('bradykinesia', 'Slowness of movement'),
  SymptomEntry('rigidity', 'Muscle stiffness'),
  SymptomEntry('postural_instability', 'Balance problems / falls'),
  SymptomEntry('loss_of_balance', 'Difficulty balancing or walking steadily'),
  SymptomEntry('shuffling_gait', 'Short, shuffling steps when walking'),
  SymptomEntry('unilateral_weakness', 'Weakness on one side of the body'),
  SymptomEntry('facial_droop', 'One side of the face drooping'),
  SymptomEntry('slurred_speech', 'Difficulty speaking clearly'),
  SymptomEntry('sudden_onset', 'Symptoms started suddenly'),
  SymptomEntry('numbness_one_side', 'Numbness on one side of the body'),
  SymptomEntry('vision_loss_one_eye', 'Vision loss or blurring in one eye'),
  SymptomEntry('double_vision', 'Seeing double'),
  SymptomEntry('severe_headache_worst_ever', "Sudden, extremely severe 'worst headache of my life'"),
  SymptomEntry('headache', 'General headache'),
  SymptomEntry('throbbing_headache_unilateral', 'Throbbing headache, usually one side'),
  SymptomEntry('nausea_with_headache', 'Nausea or vomiting alongside headache'),
  SymptomEntry('light_sensitivity', 'Sensitivity to light'),
  SymptomEntry('sound_sensitivity', 'Sensitivity to sound'),
  SymptomEntry('visual_aura', 'Visual disturbances (flashing lights, zigzag lines) before/during headache'),
  SymptomEntry('seizure_convulsive', 'Convulsive seizure (shaking, loss of consciousness)'),
  SymptomEntry('seizure_staring_episode', 'Brief staring spells / lapses in awareness'),
  SymptomEntry('post_seizure_confusion', 'Confusion after an episode'),
  SymptomEntry('memory_loss_gradual', 'Gradual, worsening memory loss'),
  SymptomEntry('confusion_gradual', 'Gradual confusion or disorientation'),
  SymptomEntry('personality_change', 'Noticeable change in personality or behavior'),
  SymptomEntry('difficulty_word_finding', 'Trouble finding the right words'),
  SymptomEntry('numbness_tingling_limbs', 'Numbness or tingling in arms/legs'),
  SymptomEntry('vision_problems_intermittent', 'Vision problems that come and go'),
  SymptomEntry('muscle_weakness_progressive', 'Progressively worsening muscle weakness'),
  SymptomEntry('fatigue_worsens_with_activity', 'Fatigue that worsens with heat or exertion'),
  SymptomEntry('muscle_twitching', 'Muscle twitching (fasciculations)'),
  SymptomEntry('muscle_wasting', 'Visible muscle wasting'),
  SymptomEntry('swallowing_difficulty', 'Difficulty swallowing'),
  SymptomEntry('facial_pain_shock_like', 'Sudden shock-like facial pain'),
  SymptomEntry('neck_stiffness', 'Stiff neck'),
  SymptomEntry('fever_with_headache', 'Fever alongside headache'),
  SymptomEntry('sensitivity_to_touch_face', 'Pain triggered by light touch to the face'),
];

/// Returns up to [limit] plain-language suggestions whose label contains any
/// word from the current (partial) input, case-insensitive.
/// Matches on the LAST word being typed, so mid-sentence typing still suggests
/// relevantly rather than trying to match the whole string.
List<SymptomEntry> matchSymptomSuggestions(String input, {int limit = 5}) {
  final trimmed = input.trimRight();
  if (trimmed.isEmpty) return [];

  // Use the last "word-ish" fragment (letters only) as the match key, so
  // "shaking at re" matches on "re" -> still weak, so also try last 2 words.
  final words = trimmed.toLowerCase().split(RegExp(r'[\s,]+'));
  final lastWord = words.isNotEmpty ? words.last : '';
  final lastTwoWords = words.length >= 2
      ? '${words[words.length - 2]} ${words.last}'
      : lastWord;

  if (lastWord.length < 2) return [];

  final scored = <MapEntry<SymptomEntry, int>>[];
  for (final entry in kSymptomVocabulary) {
    final label = entry.plainLabel.toLowerCase();
    final tag = entry.tag.toLowerCase();
    int score = -1;
    if (label.contains(lastTwoWords) || tag.contains(lastTwoWords.replaceAll(' ', '_'))) {
      score = 2;
    } else if (label.contains(lastWord) || tag.contains(lastWord)) {
      score = 1;
    }
    if (score >= 0) scored.add(MapEntry(entry, score));
  }

  scored.sort((a, b) => b.value.compareTo(a.value));
  return scored.take(limit).map((e) => e.key).toList();
}
