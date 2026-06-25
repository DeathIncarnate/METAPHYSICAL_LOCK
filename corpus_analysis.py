# corpus_analysis.py
import matplotlib.pyplot as plt
import numpy as np

def visualize_corpus_patterns(corpus_phrases):
    """Visualize the Wolfram rule patterns in the corpus"""
    
    # Convert phrases to Wolfram rules
    all_rules = []
    for phrase in corpus_phrases:
        rules = phrase_to_wolfram_rules(phrase)
        all_rules.extend(rules)
    
    # Create histogram of rule frequencies
    rule_counts = {}
    for rule in all_rules:
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
    
    # Prepare data for plotting
    rules = list(rule_counts.keys())
    counts = [rule_counts[rule] for rule in rules]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Rule frequency distribution
    ax1.bar(rules[:20], counts[:20])  # Top 20 rules
    ax1.set_xlabel('Wolfram Rule Number')
    ax1.set_ylabel('Frequency in Corpus')
    ax1.set_title('Top 20 Wolfram Rules in Corpus')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Rule class distribution
    rule_classes = {
        'Class I (Homogeneous)': 0,
        'Class II (Periodic)': 0, 
        'Class III (Chaotic)': 0,
        'Class IV (Complex)': 0,
        'Unclassified': 0
    }
    
    for rule in all_rules:
        if rule in [0, 8, 32, 40, 128, 136, 160, 168]:
            rule_classes['Class I (Homogeneous)'] += 1
        elif rule in [4, 12, 36, 44, 72, 76, 100, 104, 132, 140, 164, 172]:
            rule_classes['Class II (Periodic)'] += 1
        elif rule in [18, 22, 26, 30, 45, 60, 73, 75, 89, 101, 105, 109, 110, 124, 129, 137, 149, 151]:
            rule_classes['Class III (Chaotic)'] += 1
        elif rule in [54, 62, 90, 94, 108, 110, 122, 126, 146, 150, 182, 188]:
            rule_classes['Class IV (Complex)'] += 1
        else:
            rule_classes['Unclassified'] += 1
    
    # Plot class distribution
    classes = list(rule_classes.keys())
    class_counts = [rule_classes[cls] for cls in classes]
    
    ax2.pie(class_counts, labels=classes, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Wolfram Rule Class Distribution in Corpus')
    
    plt.tight_layout()
    plt.savefig('corpus_wolfram_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print insights
    total_rules = len(all_rules)
    print(f"\n📊 CORPUS ANALYSIS INSIGHTS:")
    print(f"   Total Wolfram rules in corpus: {total_rules}")
    print(f"   Unique Wolfram rules: {len(rule_counts)}")
    print(f"   Most common rule: {max(rule_counts, key=rule_counts.get)}")
    print(f"   Rule class distribution: {rule_classes}")

if __name__ == "__main__":
    visualize_corpus_patterns(CORPUS_PHRASES)
