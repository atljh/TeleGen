module.exports = {
    extends: ['@commitlint/config-conventional'],
    rules: {
      'type-enum': [
        2,
        'always',
        [
          'feat',
          'fix',
          'docs',
          'style',
          'refactor',
          'test',
          'chore',
          'perf',
          'ci',
          'revert',
          'build'
        ]
      ],
      'subject-case': [0],
      'header-max-length': [2, 'always', 100]
    }
  };
