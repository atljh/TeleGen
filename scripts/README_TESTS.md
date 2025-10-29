# Test Scripts for TeleGen

Scripts for testing post generation and flow management.

## Available Scripts

### 1. test_post_generation.py - Basic Testing

Creates random or exact number of test posts.

```bash
# List available flows
python scripts/test_post_generation.py --list

# Create random number of posts (5-15)
python scripts/test_post_generation.py --flow-id 1

# Create exact number
python scripts/test_post_generation.py --flow-id 1 --exact 10

# Create random in range
python scripts/test_post_generation.py --flow-id 1 --min-posts 3 --max-posts 8

# Delete test posts
python scripts/test_post_generation.py --flow-id 1 --delete
```

### 2. test_flow_scenarios.py - Scenario Testing

Tests complex scenarios and edge cases.

Available scenarios:
- `overflow` - Creates 2x flow_volume posts
- `publish-cycle` - Tests create → publish → create cycle
- `schedule` - Tests post scheduling
- `edge-cases` - Tests boundary conditions
- `all` - Runs all scenarios

```bash
# Run overflow test
python scripts/test_flow_scenarios.py --flow-id 1 --scenario overflow

# Run all scenarios
python scripts/test_flow_scenarios.py --flow-id 1 --scenario all
```

## Makefile Commands

### Basic Commands

```bash
# List flows
make test-flows

# Generate posts
make test-gen-random FLOW_ID=2
make test-gen-exact FLOW_ID=2 COUNT=10
make test-gen-range FLOW_ID=2 MIN=5 MAX=20

# Run scenarios
make test-scenario-overflow FLOW_ID=2
make test-scenario-publish FLOW_ID=2
make test-scenario-schedule FLOW_ID=2
make test-scenario-edge FLOW_ID=2
make test-scenario-all FLOW_ID=2

# Cleanup
make test-gen-clean FLOW_ID=2
```

### Quick Shortcuts (for flow 1)

```bash
make test-quick         # Create 10 posts
make test-overflow      # Create 50 posts
make test-full          # Run all scenarios
make test-clean-all     # Delete all test posts
```

### Help

```bash
make test-help
```

## Test Scenarios

### Scenario 1: Basic Test

```bash
make test-flows
make test-gen-exact FLOW_ID=1 COUNT=10
# Check bot displays flow_volume posts
make test-gen-clean FLOW_ID=1
```

### Scenario 2: Overflow Test

```bash
make test-gen-exact FLOW_ID=1 COUNT=100
# Check bot still shows only flow_volume posts
# Database contains all 100 posts
make test-gen-clean FLOW_ID=1
```

### Scenario 3: Publish Cycle

```bash
make test-gen-exact FLOW_ID=1 COUNT=10
# Manually publish 5 posts in bot
make test-gen-exact FLOW_ID=1 COUNT=10
# Check: 5 published + 15 drafts in database
# Bot shows flow_volume drafts
make test-gen-clean FLOW_ID=1
```

### Scenario 4: Full Test Suite

```bash
make test-full
# Runs all scenarios automatically
# Cleans up test data at the end
```

## What to Check

### In Bot Dialog
- Shows only flow_volume posts
- Displays newest posts first
- Pagination works correctly

### In Logs
```
Flow 'TestFlow' (id=1): created 10 new posts
Statistics: drafts=50, published=20, scheduled=5
Dialog shows last 10 drafts
```

### In Database
```bash
docker-compose exec admin_panel python manage.py shell
>>> from admin_panel.models import Post, Flow
>>> flow = Flow.objects.get(id=1)
>>> Post.objects.filter(flow=flow, status='draft').count()
```

## Troubleshooting

### Script Not Running

```bash
cd /Users/fyodorlukashov/Music/TeleGen
source .venv/bin/activate
pip install -r requirements.txt
python scripts/test_post_generation.py --list
```

### Flow Not Found

```bash
python scripts/test_post_generation.py --list
python scripts/test_post_generation.py --flow-id 1
```

### Too Many Test Posts

```bash
python scripts/test_post_generation.py --flow-id 1 --delete

# Or via Django shell
docker-compose exec admin_panel python manage.py shell
>>> from admin_panel.models import Post
>>> Post.objects.filter(source_id__startswith='test_').delete()
```

## Notes

- Test posts have source_id starting with `test_`
- Scripts use timestamp + random ID for uniqueness
- Test posts don't conflict with real posts
- `--delete` removes only test posts
- Real posts are never deleted automatically

## Aliases

```bash
alias test-list='python scripts/test_post_generation.py --list'
alias test-quick='python scripts/test_post_generation.py --flow-id 1 --exact 10'
alias test-full='python scripts/test_flow_scenarios.py --flow-id 1 --scenario all'
alias test-clean='python scripts/test_post_generation.py --flow-id 1 --delete'
```

## Checklist

- [ ] Dialog shows correct number of posts (flow_volume)
- [ ] Published posts remain in database
- [ ] Scheduled posts separate from drafts
- [ ] New posts added without errors
- [ ] Logs show correct statistics
- [ ] Pagination works correctly
- [ ] Test data cleaned after completion
