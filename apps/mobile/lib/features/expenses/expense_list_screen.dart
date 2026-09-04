import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/auth_controller.dart';
import '../../core/data_providers.dart';
import 'expense_form.dart';

class ExpenseListScreen extends ConsumerWidget {
  const ExpenseListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expenses = ref.watch(expensesProvider);
    final categories = ref.watch(categoriesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Expenses'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/dashboard'),
        ),
      ),
      body: expenses.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Failed to load: $e')),
        data: (page) {
          if (page.items.isEmpty) {
            return const Center(
              child: Text('No expenses yet. Tap + to add one.'),
            );
          }
          final categoryNames = <String, String>{};
          categories.whenData((cats) {
            for (final c in cats) {
              categoryNames[c.id] = c.name;
              for (final sub in c.children) {
                categoryNames[sub.id] = '${c.name} › ${sub.name}';
              }
            }
          });

          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(expensesProvider),
            child: ListView.builder(
              itemCount: page.items.length,
              itemBuilder: (context, index) {
                final e = page.items[index];
                return Dismissible(
                  key: Key(e.id),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 16),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),
                  confirmDismiss: (_) async {
                    return await showDialog<bool>(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: const Text('Delete expense?'),
                        content: Text('Delete "${e.description}"?'),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(ctx, false),
                            child: const Text('Cancel'),
                          ),
                          FilledButton(
                            onPressed: () => Navigator.pop(ctx, true),
                            child: const Text('Delete'),
                          ),
                        ],
                      ),
                    );
                  },
                  onDismissed: (_) async {
                    final api = ref.read(apiClientProvider);
                    await api.dio.delete('/api/v1/expenses/${e.id}');
                    ref.invalidate(expensesProvider);
                  },
                  child: ListTile(
                    title: Text(e.description),
                    subtitle: Text(
                      '${categoryNames[e.categoryId] ?? "Uncategorized"} · '
                      '${DateFormat.yMMMd().format(e.expenseDate)}',
                    ),
                    trailing: Text(
                      '${e.amount} ${e.currency}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    onTap: () => showModalBottomSheet(
                      context: context,
                      isScrollControlled: true,
                      builder: (_) => ExpenseForm(expense: e),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => showModalBottomSheet(
          context: context,
          isScrollControlled: true,
          builder: (_) => const ExpenseForm(),
        ),
        child: const Icon(Icons.add),
      ),
    );
  }
}
