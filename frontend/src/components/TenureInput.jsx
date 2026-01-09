import React from 'react';
import SkillsSelection from './SkillsSelection';

const TenureInput = ({
  selectedSkills = [],
  tenureData = {},
  onTenureChange,
  onSkillsChange,
  placeholder = "Select skills for tenure tracking..."
}) => {
  const handleSkillSelectionChange = (skills) => {
    // When skills change, we need to clean up tenure data for skills that are no longer selected
    const newTenureData = {};
    skills.forEach(skill => {
      if (tenureData[skill] !== undefined) {
        newTenureData[skill] = tenureData[skill];
      }
    });
    onTenureChange(newTenureData);
  };

  const handleTenureChange = (skill, years, months) => {
    // Convert years and months to total months
    const totalMonths = (parseInt(years) || 0) * 12 + (parseInt(months) || 0);

    const newTenureData = {
      ...tenureData,
      [skill]: totalMonths
    };

    // Remove tenure entry if both fields are empty
    if (totalMonths === 0) {
      delete newTenureData[skill];
    }

    onTenureChange(newTenureData);
  };

  const getTenureForSkill = (skill) => {
    const totalMonths = tenureData[skill] || 0;
    return {
      years: Math.floor(totalMonths / 12),
      months: totalMonths % 12
    };
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Company Tenure Skills
        </label>
        <p className="text-xs text-gray-500 mb-3">
          Select the skills for which you want to track company-specific tenure
        </p>

        {/* Skills selection for tenure tracking */}
        <SkillsSelection
          selectedSkills={selectedSkills}
          onSkillsChange={onSkillsChange || handleSkillSelectionChange}
          placeholder={placeholder}
        />
      </div>

      {selectedSkills.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tenure at Company (in months)
          </label>

          <div className="space-y-3">
            {selectedSkills.map((skill, index) => {
              const tenure = getTenureForSkill(skill);

              return (
                <div key={index} className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">{skill}</span>
                    <span className="text-xs text-gray-500">
                      Total: {tenure.years * 12 + tenure.months} months
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Years at Company
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="50"
                        value={tenure.years}
                        onChange={(e) => handleTenureChange(skill, e.target.value, tenure.months)}
                        className="w-full px-2 py-1 text-sm bg-white border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-black"
                        placeholder="0"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Months at Company
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="11"
                        value={tenure.months}
                        onChange={(e) => handleTenureChange(skill, tenure.years, e.target.value)}
                        className="w-full px-2 py-1 text-sm bg-white border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-black"
                        placeholder="0"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default TenureInput;